import flet as ft
import flet_video as fv
import flet.fastapi as flet_fastapi
from fastapi import FastAPI
from contextlib import asynccontextmanager
from fastapi.responses import FileResponse
from subtitle_generator import SubtitleGenerator
import toml

try:
    config = toml.load('config.toml')
except FileNotFoundError:
    with open('config.toml','w+') as f:
        f.write('''
token = "YOUR_TOKEN_HERE" # Hugging Face Token
storage_path = './storage'# 文件存储路径
models_path = './models'  # 模型存放路径
whisper_model = 'large-v3-turbo' # Whisper 模型
''')
    print('Please change the config.toml with your own Hugging Face Token')
    exit(0)

subtitle_generator = SubtitleGenerator(token=config['token'],cache_dir=config['models_path'])
subtitle_generator.load_models(whisper_model=config['whisper_model'])
import os
os.environ['FLET_SECRET_KEY']=str(os.urandom(24))
os.environ['FLET_FORCE_WEB_SERVER']="true"

@asynccontextmanager
async def lifespan(app: FastAPI):
    await flet_fastapi.app_manager.start()
    yield
    await flet_fastapi.app_manager.shutdown()

app = FastAPI(lifespan=lifespan)

async def main(page: ft.Page):
    page.title="视频字幕生成器"
    page.horizontal_alignment=ft.CrossAxisAlignment.CENTER
    
    def pick_files_result(e: ft.FilePickerResultEvent):
        if not e.files:
            return
        upload_button.disabled=False
        generate_button.disabled=True
        download_button.disabled=True
        selected_files.value = f'当前选择：{e.files[0].name}'
        selected_files.data = e.files[0].name
        error.value = '确认选择的文件无误后，点击“上传文件”。'
        page.update()
    def upload_progress(e:ft.FilePickerUploadEvent):
        progress_bar.value=e.progress
        progress_bar.update()
        if e.progress == 1:
            pick_files_button.disabled=False
            upload_button.disabled=True
            generate_button.disabled=False
            download_button.disabled=True
            error.value='点击“开始生成”即可开始生成字幕。'
            try:
                video.playlist_remove(0)
            except:
                ...
            video.playlist_add(fv.VideoMedia(f'/video/{selected_files.data}'))
            video.next()
            page.update()
    pick_files_dialog = ft.FilePicker(on_result=pick_files_result,on_upload=upload_progress)
    page.overlay.append(pick_files_dialog)
    

    video = fv.Video(expand=True,aspect_ratio= 16 / 9,playlist_mode=fv.PlaylistMode.SINGLE)
    # subtitle = ft.Text(value='生成的字幕将显示于此。',text_align=ft.TextAlign.CENTER)

    error = ft.Text('请点击“选择视频文件”按钮选择您要上传的文件。',text_align=ft.TextAlign.CENTER)
    
    pick_files_button = ft.ElevatedButton(
        "选择视频文件",
        icon=ft.Icons.FOLDER_OPEN,
        on_click=lambda _: pick_files_dialog.pick_files(
            allow_multiple=False,
            file_type=ft.FilePickerFileType.VIDEO
        ),
    )

    def upload_files(e):
        pick_files_button.disabled=True
        upload_button.disabled=True
        generate_button.disabled=True
        download_button.disabled=True
        page.update()
        if pick_files_dialog.result and (f:=pick_files_dialog.result.files):
            pick_files_dialog.upload([ft.FilePickerUploadFile(f[0].name, upload_url=page.get_upload_url(f'temp/{f[0].name}',60))])
            
    upload_button = ft.ElevatedButton('上传文件',icon=ft.Icons.UPLOAD,disabled=True,on_click=upload_files)
    selected_files = ft.Text('当前选择：无')
    progress_bar = ft.ProgressRing(value=0,bgcolor="#eeeeee", width=20, height=20)

    def generate(e):
        error.value = '请稍候，正在生成...'
        pick_files_button.disabled=True
        upload_button.disabled=True
        generate_button.disabled=True
        download_button.disabled=True
        page.update()
        path = config['storage_path']+'/temp/'+selected_files.data
        print(path)
        # from time import sleep
        # sleep(10)
        def progress(p:int,q:int) -> None:
            progress_bar.value = p / q
            progress_bar.update()
        try:
            subtitle_generator.generate(path, path + '.srt',progress)
        except Exception as e:
            error.value = f'生成失败！{e}'
        else:
            error.value = '生成成功！点击“下载字幕”以下载字幕。'
            # video.subtitle_configuration=fv.VideoSubtitleConfiguration(src=f'/subtitle/{selected_files.data}',title='Subtitle',language='en',text_style=ft.TextStyle(20),text_align=ft.TextAlign.CENTER,padding=10,visible=True)
        pick_files_button.disabled=False
        upload_button.disabled=True
        generate_button.disabled=False
        download_button.disabled=False
        page.update()


    generate_button = ft.ElevatedButton("开始生成",icon=ft.Icons.GENERATING_TOKENS,on_click=generate,disabled=True)
    download_button = ft.ElevatedButton('下载字幕',icon=ft.Icons.DOWNLOAD,on_click=lambda _:page.launch_url(f'/subtitle/{selected_files.data}'),disabled=True)

    page.add(
        error,
        ft.Row(
            [
                pick_files_button,
                upload_button,
                progress_bar,
                selected_files,
                generate_button,
                download_button
            ],
            alignment=ft.MainAxisAlignment.CENTER
        ),
        video
    )

@app.get("/subtitle/{filename}")
def get_subtitle(filename: str):
    path = config['storage_path']+'/temp/'+filename+'.srt'
    return FileResponse(path)
@app.get('/video/{filename}')
def get_video(filename: str):
    path = config['storage_path']+'/temp/'+filename
    return FileResponse(path)
app.mount('/',flet_fastapi.app(main,upload_dir=config['storage_path']))

