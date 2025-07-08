import flet as ft
import flet_video as fv

def main(page: ft.Page):
    page.title="视频字幕生成器"
    page.horizontal_alignment=ft.CrossAxisAlignment.CENTER

    def pick_files_result(e: ft.FilePickerResultEvent):
        if e.files:
            selected_files.value = f'当前选择：{e.files[0].name}'
            selected_files.update()

    pick_files_dialog = ft.FilePicker(on_result=pick_files_result)
    selected_files = ft.Text()

    page.overlay.append(pick_files_dialog)

    page.add(
        video := fv.Video(
            expand=True,
            aspect_ratio= 16 / 9,
        ),
        ft.Text('这里将会显示字幕',text_align=ft.TextAlign.CENTER),
        ft.Row(
            [
                ft.ElevatedButton(
                    "选择视频文件",
                    icon=ft.Icons.UPLOAD_FILE,
                    on_click=lambda _: pick_files_dialog.pick_files(
                        allow_multiple=False,
                        file_type=ft.FilePickerFileType.VIDEO
                    ),
                ),
                selected_files,
            ],
            alignment=ft.MainAxisAlignment.CENTER
        )
    )

ft.app(main)
