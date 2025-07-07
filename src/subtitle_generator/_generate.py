from time import time
import torch, torchaudio
from transformers import Wav2Vec2Processor, Wav2Vec2ForCTC
from pyannote.audio import Pipeline
from moviepy.video.io.VideoFileClip import VideoFileClip
import os, re
from datetime import timedelta
print('Imported.')
def mytimer(func: function):
    def ret(*args,**kwargs):
        start_time=time()
        retv=func(*args,**kwargs)
        print(f'Duration of {func.__name__}: {time()-start_time}s')
        return retv
    return ret

class SubtitleGenerator(object):
    def __init__(self,token,device='cuda' if torch.cuda.is_available() else 'cpu'):
        self.device=torch.device(device)
        self.token=token
        self.asr_processor=None
        self.asr_model=None
        self.diarization_pipeline=None
        print(f'{self.device=}\n{self.token=}')

    def load_models(self):
        print('Loading speech recognition model...')
        self.asr_processor=Wav2Vec2Processor.from_pretrained("facebook/wav2vec2-large-960h-lv60-self")
        self.asr_model=Wav2Vec2ForCTC.from_pretrained("facebook/wav2vec2-large-960h-lv60-self").to(self.device)
        print(f'Loading speaker diarization model...')
        self.diarization_pipeline = Pipeline.from_pretrained(
            "pyannote/speaker-diarization-3.1",
            use_auth_token=self.token
        )

    def generate(self, src_video:str, dist_subtitle:str):
        # 提取音频与获取音频时长
        print('STEP 1: Extract audio...')
        mid_audio='temp_audio.wav'
        video=VideoFileClip(src_video)
        video.audio.write_audiofile(mid_audio,fps=16000,codec='pcm_s16le')
        audio_duration=video.audio.duration
        video.close()

        # 区分说话人
        print("STEP 2: Diarize speakers...")
        diarization=self.diarization_pipeline(mid_audio)
        speaker_segments=list()
        for segment, _, speaker in diarization.itertracks(yield_label=True):
            speaker_segments.append({
                "start": segment.start,
                "end": segment.end,
                "speaker": speaker
            })
        
        # 语音识别
        ('STEP 3: Transcribe audio...')
        waveform, sample_rate=torchaudio.load(mid_audio)
        if sample_rate!=16000:
            resampler=torchaudio.transforms.Resample(sample_rate)
            waveform=resampler(waveform)
        
        input_values=self.asr_processor(
            waveform.squeeze().numpy(),
            sampling_rate=16000,
            return_tensors='pt'
        ).input_values.to(self.device)

        with torch.no_grad():
            logits=self.asr_model(input_values).logits
        
        predicted_ids=torch.argmax(logits,dim=-1)
        transcription=self.asr_processor.batch_decode(predicted_ids)[0].lower()
        print(transcription)

        # 对齐文本与说话人
        print('STEP 4: Align transcription with speaker segments...')
        words=re.findall(r'\b\w+\b',transcription)
        word_duration=audio_duration/len(words)

        word_timestamps=list()
        for i,word in enumerate(words):
            begin_time=i*word_duration
            end_time=(i+1)*word_duration
            word_timestamps.append({
                "word":word,
                "start":begin_time,
                "end":end_time
            })

        aligned_segments=list()
        for segment in speaker_segments:
            segment_text=list()
            for word in word_timestamps:
                if word["start"]>=segment['start'] and word['end']<segment['end']:
                    segment_text.append(word['word'])
            
            if segment_text:
                aligned_segments.append({
                    "speaker": segment["speaker"],
                    "start": segment['start'],
                    "end": segment["end"],
                    "text": " ".join(segment_text)
                })

        
        # 生成字幕
        print('STEP 5: Output into SRT files...')
        with open(dist_subtitle,"w",encoding='utf-8') as f:
            def format_timedelta(td: timedelta):
                hours=td.seconds//3600
                minutes=td.seconds%60//60
                seconds=td.seconds%60%60
                ms=td.microseconds//1000
                return f'{hours:02}:{minutes:02}:{seconds:02}, {ms:03}'
            for i,segment in enumerate(aligned_segments,1):
                begin_time=timedelta(seconds=segment['start'])
                end_time=timedelta(seconds=segment['end'])

                f.writelines((f"{i}\n",
                f'{format_timedelta(begin_time)} --> {format_timedelta(end_time)}\n',
                f'[{segment['speaker']}] {segment['text']}\n\n'))

        # 清理临时文件
        print('STEP 6: Clean temporary files...')
        os.remove(mid_audio)

        print(f"Done...\n\tSrc: {src_video}\n\tDist:{dist_subtitle}")

if __name__=='__main__':
    with open('TOKEN','r') as f:
        token=f.readline()
    generator=SubtitleGenerator(token)
    generator.load_models()
    generator.generate('test.mp4','test.src')