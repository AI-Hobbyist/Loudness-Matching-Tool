import os
import subprocess
import shutil
from pydub import AudioSegment
import pyloudnorm
import numpy as np
import json
import argparse

FFMPEG = './ffmpeg/ffmpeg.exe'


def load_config(config_file):
    with open(config_file, 'r') as f:
        return json.load(f)


def convert_to_wav(input_file, output_file, config):
    startupinfo = subprocess.STARTUPINFO()
    startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
    startupinfo.wShowWindow = subprocess.SW_HIDE

    if config["ffmpeg_bit_depth"] == 16:
        encoder = "pcm_s16le"
    elif config["ffmpeg_bit_depth"] == 24:
        encoder = "pcm_s24le"
    elif config["ffmpeg_bit_depth"] == 32:
        encoder = "pcm_s32le"

    with open(os.devnull, 'w') as devnull:
        subprocess.run([FFMPEG, '-i', input_file, '-ar',
                        str(config["ffmpeg_sample_rate"]), '-c:a', encoder, '-y', output_file],
                       stdout=devnull, stderr=subprocess.STDOUT, startupinfo=startupinfo)


def export_audio(adjusted_audio, output_path, temp_dir, export_format, mp3_bitrate, ffmpeg_sample_rate):
    # 因为pydub的导出无法指定ffmpeg路径并且打包出来的程序在运行时会有控制台窗口闪烁，所以当转换为其他格式时，先保存为wav格式，再调用ffmpeg进行格式转换
    # 也有可能是我太菜了，轻喷
    startupinfo = subprocess.STARTUPINFO()
    startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
    startupinfo.wShowWindow = subprocess.SW_HIDE

    if export_format == "mp3":
        temp_dir = os.path.join(temp_dir, "temp.wav")
        adjusted_audio.export(temp_dir, format="wav")
        with open(os.devnull, 'w') as devnull:
            subprocess.run([FFMPEG, "-i", "./temp/temp.wav", "-ar", str(ffmpeg_sample_rate), "-b:a", str(mp3_bitrate)+"k",
                           "-f", "mp3", '-y', output_path], stdout=devnull, stderr=subprocess.STDOUT, startupinfo=startupinfo)
    if export_format == "flac":
        temp_dir = os.path.join(temp_dir, "temp.wav")
        adjusted_audio.export(temp_dir, format="wav")
        with open(os.devnull, 'w') as devnull:
            subprocess.run([FFMPEG, "-i", "./temp/temp.wav", "-ar", str(ffmpeg_sample_rate), "-f", "flac", '-y', output_path],
                           stdout=devnull, stderr=subprocess.STDOUT, startupinfo=startupinfo)
    if export_format == "wav":
        adjusted_audio.export(output_path, format="wav")


def match_lufs(input_file, target_lufs, output_dir, temp_dir, config):
    audio = AudioSegment.from_file(input_file)
    bit_depth = audio.sample_width * 8

    normalization_factor = 2 ** (bit_depth - 1)
    y = np.array(audio.get_array_of_samples(),
                 dtype=np.float32) / normalization_factor
    sr = audio.frame_rate

    meter = pyloudnorm.Meter(sr)
    current_lufs = meter.integrated_loudness(y)

    gain = target_lufs - current_lufs
    adjusted_audio = audio + gain

    filename, ext = os.path.splitext(os.path.basename(input_file))
    output_filename = f"{filename}_to{target_lufs:.2f}LUFS.{config['export_format']}"
    output_path = os.path.join(output_dir, output_filename)

    export_audio(adjusted_audio, output_path, temp_dir,
                 config['export_format'], config['mp3_bitrate'], config['ffmpeg_sample_rate'])


def match_average_dbfs(input_file, target_average_dbfs, output_dir, temp_dir, config):
    audio = AudioSegment.from_file(input_file)
    current_average_dbfs = audio.dBFS

    gain = target_average_dbfs - current_average_dbfs
    adjusted_audio = audio + gain
    filename, ext = os.path.splitext(os.path.basename(input_file))

    output_filename = f"{filename}_to{target_average_dbfs:.2f}AVE_dBFS.{config['export_format']}"
    output_path = os.path.join(output_dir, output_filename)

    export_audio(adjusted_audio, output_path, temp_dir,
                 config['export_format'], config['mp3_bitrate'], config['ffmpeg_sample_rate'])


def match_peak_dbfs(input_file, target_peak_dbfs, output_dir, temp_dir, config):
    # pydub只能计算peak，无法计算true peak，所以只能匹配最大峰值，实际最大峰值没法匹配
    audio = AudioSegment.from_file(input_file)
    current_peak_dbfs = audio.max_dBFS

    gain = target_peak_dbfs - current_peak_dbfs
    adjusted_audio = audio + gain
    filename, ext = os.path.splitext(os.path.basename(input_file))

    output_filename = f"{filename}_to{target_peak_dbfs:.2f}Peak_dBFS.{config['export_format']}"
    output_path = os.path.join(output_dir, output_filename)

    export_audio(adjusted_audio, output_path, temp_dir,
                 config['export_format'], config['mp3_bitrate'], config['ffmpeg_sample_rate'])


def match_rms(input_file, target_rms_db, output_dir, temp_dir, config):
    audio = AudioSegment.from_file(input_file)

    y = np.array(audio.get_array_of_samples(), dtype=np.float32)
    rms = np.sqrt(np.mean(y ** 2))

    target_rms = 10 ** (target_rms_db / 20)
    gain = target_rms / rms
    adjusted_audio = audio.apply_gain(gain)

    filename, ext = os.path.splitext(os.path.basename(input_file))
    output_filename = f"{filename}_to{target_rms_db:.2f}RMSdB.{config['export_format']}"
    output_path = os.path.join(output_dir, output_filename)

    export_audio(adjusted_audio, output_path, temp_dir,
                 config['export_format'], config['mp3_bitrate'], config['ffmpeg_sample_rate'])


def process_audio(input_dir, output_dir, target_loudness, loudness_type="LUFS", progress_callback=None):
    config = load_config("config.json")

    temp_dir = 'temp'
    os.makedirs(temp_dir, exist_ok=True)

    audio_files = [f for f in os.listdir(input_dir) if not f.startswith('.')]

    for i, file in enumerate(audio_files):
        input_file = os.path.join(input_dir, file)

        if not input_file.lower().endswith('.wav'):
            output = os.path.join(
                temp_dir, f"{os.path.splitext(file)[0]}.wav")
            convert_to_wav(input_file, output, config)
            input_file = output

        if loudness_type == "ITU-R BS.1770 (LUFS)":
            match_lufs(input_file, target_loudness,
                       output_dir, temp_dir, config)
        elif loudness_type == "平均响度 (dBFS)":
            match_average_dbfs(input_file, target_loudness,
                               output_dir, temp_dir, config)
        elif loudness_type == "最大峰值 (dBFS)":
            match_peak_dbfs(input_file, target_loudness,
                            output_dir, temp_dir, config)
        elif loudness_type == "总计 RMS (dB)":
            match_rms(input_file, target_loudness,
                      output_dir, temp_dir, config)

        if progress_callback:
            progress_callback(int((i + 1) / len(audio_files) * 100))

    shutil.rmtree(temp_dir)


def main():
    parser = argparse.ArgumentParser(description="Audio processing API")
    parser.add_argument("-i", "--input_dir", type=str, required=True,
                        help="Input directory containing audio files")
    parser.add_argument("-o", "--output_dir", type=str, required=True,
                        help="Output directory to save processed audio files")
    parser.add_argument("target_loudness", type=float,
                        default=-23, help="Target loudness  (default: -23)")
    parser.add_argument("-type", "--loudness_type", type=str, default="LUFS", choices=["LUFS", "dBFS", "Peak_dBFS", "RMSdB"],
                        help="Type of loudness to match (default: LUFS)")
    parser.add_argument("--export_format", type=str, default="wav", choices=["wav", "flac", "mp3"],
                        help="Audio export format (default: wav)")
    parser.add_argument("--mp3_bitrate", type=int, default=320, choices=[128, 192, 256, 320],
                        help="MP3 bitrate in kbps (default: 320)")
    parser.add_argument("--ffmpeg_sample_rate", type=int, default=48000, choices=[32000, 44100, 48000],
                        help="Output audio sample rate (default: 48000)")
    parser.add_argument("--ffmpeg_bit_depth", type=int, default=32, choices=[16, 24, 32],
                        help="Output audio bit depth (default: 32)")

    args = parser.parse_args()

    print("Input directory:{}, Output directory:{}, Target loudness:{}, Loudness type:{}, Export format:{}, MP3 bitrate:{}, FFMPEG sample rate:{}, FFMPEG bit depth:{}".format(
        args.input_dir, args.output_dir, args.target_loudness, args.loudness_type, args.export_format, args.mp3_bitrate, args.ffmpeg_sample_rate, args.ffmpeg_bit_depth
    ))

    with open('config.json', 'r') as config_file:
        config = json.load(config_file)

    config["export_format"] = args.export_format
    config["mp3_bitrate"] = args.mp3_bitrate
    config["ffmpeg_sample_rate"] = args.ffmpeg_sample_rate
    config["ffmpeg_bit_depth"] = args.ffmpeg_bit_depth

    with open('config.json', 'w') as config_file:
        json.dump(config, config_file, indent=4)

    if args.loudness_type == "LUFS":
        loudness_type = "ITU-R BS.1770 (LUFS)"
    elif args.loudness_type == "dBFS":
        loudness_type = "平均响度 (dBFS)"
    elif args.loudness_type == "Peak_dBFS":
        loudness_type = "最大峰值 (dBFS)"
    elif args.loudness_type == "RMSdB":
        loudness_type = "总计 RMS (dB)"

    process_audio(args.input_dir, args.output_dir,
                  args.target_loudness, loudness_type)


if __name__ == "__main__":
    main()
