<div align="center">

# Loudness Matching Tool

[English](./README.md) | 繁體中文

</div>

基於 PyQt5 寫的一個音頻響度匹配小工具，目前支援 ITU-R BS.1770 (LUFS), 平均響度 (dBFS), 最大峰值 (dBFS), 總計 RMS (dB), 四種匹配方式。

## 安裝發行版

你可以直接前往 [releases](https://github.com/SUC-DriverOld/Loudness-Matching-Tool/releases) 下載安裝程式或解壓直用版。

## 從源碼啟動

1. 克隆本倉庫

```bash
git clone https://github.com/SUC-DriverOld/Loudness-Matching-Tool.git
```

2. 安裝依賴

```bash
pip install -r requirements.txt
```

3. 下載 [ffmpeg](https://ffmpeg.org/) 並將 `ffmpeg.exe` 放置到 `./ffmpeg` 目錄下

4. 使用 `gui.py` 啟動

```bash
python gui.py
```

## 使用命令列

使用`audio_processor.py`：

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

例如：

```bash
python audio_processor.py -i input -o output -target -23 -type LUFS --export_format mp3 --mp3_bitrate 320
```

## 一些說明

1. 目前支援的響度匹配有以下四種：

   - ITU-R BS.1770 (LUFS)
   - 平均響度 (dBFS)
   - 最大峰值 (dBFS)【不是最大 **實際** 峰值！】
   - 總計 RMS (dB)

2. 導出格式支援：

   - 支援的導出音頻格式：`wav`, `mp3`, `flac`
   - 支援設定導出 mp3 比特率：`320k`, `256k`, `192k`, `128k`
   - 支援設定導出採樣率：`32000Hz`, `44100Hz`, `48000Hz`
   - 支援設定導出位深度：`16bit`, `24bit`, `32 bit float`

3. 由於格式轉換是調用 ffmpeg 來實現的，所以有一些格式導出處理會較慢，具體實現方式如下：

   - 導入 wav 格式 -> 匹配響度 -> 導出 wav 格式
   - 導入 wav 格式 -> 匹配響度 -> 先導出 wav 格式 -> 再調用 ffmpeg 導出 mp3 或 flac 格式
   - 導入 mp3 或 flac 格式 -> 匹配響度 -> 導出 wav 格式
   - 導入 mp3 或 flac 格式 -> 匹配響度 -> 先導出 wav 格式 -> 再調用 ffmpeg 導出 mp3 或 flac 格式

> [!NOTE]
>
> 因此，此處建議導入和導出格式都採用 wav，會大大加快處理時間！

## 存在的問題

**如果有佬能解決這些問題的話，歡迎提出 pull request，感激不盡！**

1. 因為 pydub 的導出無法指定 ffmpeg 路徑並且打包出來的程式在運行時會有控制台視窗閃爍，所以當轉換為其他格式時，採用的方法是先保存為 wav 格式，再調用 ffmpeg 進行格式轉換。導出操作的部分程式碼如下。也有可能是我太菜了，輕噴。詳情請見 [audio_processor.py#L35](https://github.com/SUC-DriverOld/Loudness-Matching-Tool/blob/main/audio_processor.py#L35)
2. pydub 只能計算 peak，無法計算 true peak，所以只能匹配最大峰值，實際最大峰值沒法匹配。詳情請見 [audio_processor.py#L96](https://github.com/SUC-DriverOld/Loudness-Matching-Tool/blob/main/audio_processor.py#L96)
3. 在實際測試中，部分電腦出現了控制台閃爍的情況。**但大部分情況下不會出現這個問題。**我暫時無法復現這個問題，所以暫時無法解決。
4. 在選擇位深度 `24bit` 導出時，有機率無法以指定的位深度導出。 