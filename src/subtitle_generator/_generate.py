from time import time
start_time=time()
import whisper, os
from pyannote.audio import Pipeline
from moviepy.video.io.VideoFileClip import VideoFileClip
from datetime import timedelta
print(f'Imported in {time()-start_time}s.')
from pprint import pprint
del start_time

def mytimer(func):
    def ret(*args,**kwargs):
        start_time=time()
        retv=func(*args,**kwargs)
        print(f'Duration of {func.__name__}: {time()-start_time}s')
        return retv
    return ret

class SubtitleGenerator(object):
    def __init__(self,token):
        self.token=token
        self.asr_processor=None
        self.asr_model=None
        self.diarization_pipeline=None
        print(f'{self.token=}')
    
    @mytimer
    def load_models(self):
        print('Loading speech recognition model...')
        self.whisper_model=whisper.load_model('large-v3-turbo',download_root='./models/whisper')
        print(f'Loading speaker diarization model...')
        self.diarization_pipeline = Pipeline.from_pretrained(
            "pyannote/speaker-diarization-3.1",
            use_auth_token=self.token,
            cache_dir='./models/pyannote'
        )

    @mytimer
    def generate(self, src_video:str, dist_subtitle:str):
        @mytimer
        def extract_audio(src_video:str, mid_audio:str):
            # 提取音频与获取音频时长
            print('STEP 1: Extract audio...')
            video=VideoFileClip(src_video)
            video.audio.write_audiofile(mid_audio,fps=16000,codec='pcm_s16le')
            video.close()

        @mytimer
        def diarize_speakers(mid_audio:str):
            # 区分说话人
            print("STEP 2: Diarize speakers...")
            diarization=self.diarization_pipeline(mid_audio)
            speaker_segments=dict()
            # 对时间段以speaker分类便于合并
            for segment, _, speaker in diarization.itertracks(yield_label=True):
                speaker_segments[speaker]=speaker_segments.get(speaker,())+((segment.start,segment.end),)
            for speaker in speaker_segments.keys():
                segments=speaker_segments[speaker]
                segments=sorted(segments, key=lambda x:x[0])
                new_segments=list()
                last_start=segments[0][0]
                last_end=segments[0][1]
                for elem in segments[1:]:
                    if elem[0]-last_end>1:
                        new_segments.append((last_start,last_end))
                        last_start=elem[0]
                    last_end=elem[1]
                    
                new_segments.append((last_start,last_end))
                speaker_segments[speaker]=new_segments
            ret=list()
            # 转为以时间作键便于后续查找对应
            for speaker, periods in speaker_segments.items():
                for period in periods:
                    ret.append({
                        'start':period[0],
                        'end':period[1],
                        'speaker':speaker
                    })
            ret=sorted(ret,key=lambda x:x['start'])
            pprint(ret)
            return ret
        
        @mytimer
        def transcribe_audio(mid_audio:str):
            # 语音识别
            print('STEP 3: Transcribe audio...')
            result=self.whisper_model.transcribe(mid_audio)
            ret=list()
            for segment in result['segments']:
                ret.append({
                    'start': segment['start'],
                    'end': segment['end'],
                    'text': segment['text']
                })
            ret=sorted(ret,key=lambda x:x['start'])
            pprint(ret)
            return ret

        @mytimer
        def align(speaker_segments:list, transcription_result:list):
            # 对齐文本与说话人
            print('STEP 4: Align transcription with speaker segments...')
            def contains(a,b):
                return (a['start']-1 <= b['start']) and (a['end']+1 >= b['end'])
            for i,line in enumerate(transcription_result):
                for j,segment in enumerate(speaker_segments):
                    if contains(segment,line):
                        line['speaker']=segment['speaker']
                        transcription_result[i]=line
                        break
                else:
                    line['speaker']='BAD_ALIGNMENT'
            print(transcription_result)
            return transcription_result
                        
        @mytimer
        def output_subtitle(dist_subtitle, aligned_segments):
            # 生成字幕
            print('STEP 5: Output into SRT files...')
            with open(dist_subtitle,"w",encoding='utf-8') as f:
                def format_timedelta(td: timedelta):
                    hours=td.seconds//60//60
                    minutes=td.seconds//60%60
                    seconds=td.seconds%60%60
                    ms=td.microseconds//1000
                    return f'{hours:02}:{minutes:02}:{seconds:02}, {ms:03}'
                for i,segment in enumerate(aligned_segments,1):
                    begin_time=timedelta(seconds=segment['start'])
                    end_time=timedelta(seconds=segment['end'])

                    f.writelines((f"{i}\n",
                    f'{format_timedelta(begin_time)} --> {format_timedelta(end_time)}\n',
                    f'[{segment['speaker']}] {segment['text']}\n\n'))
        @mytimer
        def clean(mid_audio):
            # 清理临时文件
            print('STEP 6: Clean temporary files...')
            os.remove(mid_audio)


        mid_audio='temp_audio.wav'
        extract_audio(src_video,mid_audio)
        output_subtitle(
            dist_subtitle=dist_subtitle,
            aligned_segments=align(
                speaker_segments=diarize_speakers(mid_audio),
                transcription_result=transcribe_audio(mid_audio)
            )
        )
        clean(mid_audio)
        print(f"Done...\n\tSrc: {src_video}\n\tDist:{dist_subtitle}")

if __name__=='__main__':
    while True:
        try:
            with open('TOKEN','r') as f:
                token=f.readline()
        except FileNotFoundError:
            path=input('>>> ')
            os.chdir(path)
        else:
            break
    
    generator=SubtitleGenerator(token)
    generator.load_models()
    generator.generate('test.mp4','test.srt')