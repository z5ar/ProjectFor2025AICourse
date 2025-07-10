import flet as ft
import flet_video as fv
# import flet_web.fastapi
# from subtitle_generator import SubtitleGenerator
import toml
try:
    config = toml.load('config.toml')
except FileNotFoundError:
    with open('config.toml','w+') as f:
        f.write('''
token = "YOUR_TOKEN_HERE" # Hugging Face Token
storage_path = './storage'# 文件存储路径
models_path = './models'  # 模型存放路径
''')
    print('Please change the config.toml with your own Hugging Face Token')
    exit(0)

# subtitle_generator = SubtitleGenerator(token=config['token'],cache_dir=config['models_path'])
# subtitle_generator.load_models()
import os
os.environ['FLET_SECRET_KEY']=str(os.urandom(24))

from fastapi import FastAPI, Response
from fastapi.responses import FileResponse

def main(page: ft.Page):
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
            upload_button.disabled=False
            generate_button.disabled=False
            download_button.disabled=True
            error.value='点击“开始生成”即可开始生成字幕。'
            page.update()
    pick_files_dialog = ft.FilePicker(on_result=pick_files_result,on_upload=upload_progress)
    page.overlay.append(pick_files_dialog)
    

    video = fv.Video(expand=True,aspect_ratio= 16 / 9)
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
        from time import sleep
        sleep(10)
        # try:
        #     subtitle_generator.generate(src_video=path,dist_subtitle=path+'.srt')
        # except Exception as e:
        #     error.value = f'生成失败！{e}'
        error.value = '生成成功！您可以在上方视频播放器预览，点击“下载字幕”以下载。'
        pick_files_button.disabled=False
        upload_button.disabled=False
        generate_button.disabled=False
        download_button.disabled=False
        page.update()


    generate_button = ft.ElevatedButton("开始生成",icon=ft.Icons.GENERATING_TOKENS,on_click=generate,disabled=True)
    download_button = ft.ElevatedButton('下载字幕',icon=ft.Icons.DOWNLOAD,on_click=lambda _:page.launch_url(f'/download/{selected_files.data}'),disabled=True)
    page.add(
        video,
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
        )
    )

app = ft.app(main,upload_dir=config['storage_path'])
# @app.get("/download/{filename}")
# def download(filename: str):
#     print('Requested.===========================')
#     path = config['storage_path']+'/temp/'+filename+'.srt'
#     return FileResponse(path)