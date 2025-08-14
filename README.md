<div align="center">

# Loudness Matching Tool

English | [简体中文](./README_zh_CN.md) | [中文](./README_zh_TW.md)

</div>

A small audio loudness matching tool written with PyQt5, currently supporting ITU-R BS.1770 (LUFS), average loudness (dBFS), maximum peak (dBFS), total RMS (dB), four matching modes.

## Installation from Releases

You can directly go to [releases](https://github.com/SUC-DriverOld/Loudness-Matching-Tool/releases) to download the installer or the portable version.

## Running from Source

1. Clone this repository

```bash
git clone https://github.com/SUC-DriverOld/Loudness-Matching-Tool.git
```

2. Install dependencies

```bash
pip install -r requirements.txt
```

3. Download [ffmpeg](https://ffmpeg.org/) and place `ffmpeg.exe` in the `./ffmpeg` directory

4. Launch using `gui.py`

```bash
python gui.py
```

## Use Command Line

Use `audio_processor.py`：

```bash
    "-i", "--input_dir", Input directory containing audio files
    "-o", "--output_dir", Output directory to save processed audio files
    "-target", "--target_loudness", default=-23, Target loudness
    "-type", "--loudness_type", default="LUFS", choices=["LUFS", "dBFS", "Peak_dBFS", "RMSdB"], Type of loudness to match
    "--export_format", default="wav", choices=["wav", "flac", "mp3"], Audio export format
    "--mp3_bitrate", default=320, choices=[128, 192, 256, 320], MP3 bitrate in kbps
    "--ffmpeg_sample_rate", default=48000, choices=[32000, 44100, 48000], Output audio sample rate
    "--ffmpeg_bit_depth", default=32, choices=[16, 24, 32], Output audio bit depth

```

Example:

```bash
python audio_processor.py -i input -o output -target -23 -type LUFS --export_format mp3 --mp3_bitrate 320
```

## Notes

1. Currently supported loudness matching methods include:

   - ITU-R BS.1770 (LUFS)
   - Average loudness (dBFS)
   - Maximum peak (dBFS) [**NOT** the True Peak!]
   - Total RMS (dB)

2. Export formats support:

   - Supported export audio formats: `wav`, `mp3`, `flac`
   - Supported mp3 bitrate settings: `320k`, `256k`, `192k`, `128k`
   - Supported sample rates for export: `32000Hz`, `44100Hz`, `48000Hz`
   - Supported bit depths for export: `16bit`, `24bit`, `32 bit float`

3. Since format conversion is implemented using ffmpeg, some format export processes may be slower. The specific implementation methods are as follows:

   - Import wav format -> match volume -> export wav format
   - Import wav format -> match volume -> export wav format first -> then call ffmpeg to export mp3 or flac format
   - Import mp3 or flac format -> match volume -> export wav format
   - Import mp3 or flac format -> match volume -> export wav format first -> then call ffmpeg to export mp3 or flac format

> [!NOTE]
>
> Therefore, it is recommended to use wav for both import and export formats here, which will greatly speed up processing time!

## Known Issues

**Pull requests are welcome if anyone can solve these issues!**

1. Due to pydub's inability to specify the ffmpeg path for export and the flashing console window when running the packaged program, the method used for format conversion when exporting to other formats is to first save as WAV format and then call ffmpeg for format conversion. Part of the code for the export operation is as follows. It may also be because I'm not skilled enough, so please bear with me. Details can be found at [audio_processor.py#L35](https://github.com/SUC-DriverOld/Loudness-Matching-Tool/blob/main/audio_processor.py#L35)
2. Pydub can only calculate peak, unable to calculate true peak, so it can only match the maximum peak, unable to match the actual maximum peak. Details can be found at [audio_processor.py#L96](https://github.com/SUC-DriverOld/Loudness-Matching-Tool/blob/main/audio_processor.py#L96)
3. In actual testing, some computers experienced flashing console windows. **However, this problem does not occur in most cases.** I am currently unable to reproduce this issue, so I cannot solve it temporarily.
4. There is a chance that when exporting with the selected bit depth `24bit`, it may not export at the specified bit depth.
