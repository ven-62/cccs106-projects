import flet as ft
from db_connection import connect_db
from mysql.connector import Error


def main(page: ft.Page):
    # configure page layout
    page.window.alignment = ft.alignment.center
    page.window.frameless = True
    page.title = 'User Login'
    page.vertical_alignment = ft.MainAxisAlignment.CENTER
    page.horizontal_alignment = ft.CrossAxisAlignment.CENTER
    page.window.height = 350
    page.window.width = 400
    page.bgcolor = ft.Colors.AMBER_ACCENT
    page.theme_mode = ft.ThemeMode.LIGHT


    # title for the login form
    login_title = ft.Text(
        'User Login',
        size=20,
        weight=ft.FontWeight.BOLD,
        font_family = 'Arial',
    )
    
    # text field for username
    username_field = ft.TextField(
        label='User name',
        hint_text='Enter your user name',
        helper_text='This is your unique identifier',
        width=300,
        autofocus=True,
        icon=ft.Icons.PERSON,
        bgcolor=ft.Colors.LIGHT_BLUE_ACCENT
    )

    # text field for password
    password_field = ft.TextField(
        label='Password',
        hint_text='Enter your password',
        helper_text='This is your secret key',
        width=300,
        password=True,
        can_reveal_password=True,
        icon=ft.Icons.PASSWORD,
        bgcolor=ft.Colors.LIGHT_BLUE_ACCENT
    )

    # defining an asynchronous function for when the user clicks the login button
    async def login_click(e):
        username = username_field.value
        password = password_field.value

        success_dialog = ft.AlertDialog(
            title=ft.Text('Login Successful', text_align=ft.TextAlign.CENTER),
            content=ft.Text(f'Welcome, {username}!', text_align=ft.TextAlign.CENTER),
            icon=ft.Icon(name=ft.Icons.CHECK_CIRCLE, color='green'),
            actions=[ft.TextButton('OK', on_click=lambda e: close_dialog(success_dialog))]
        )

        failure_dialog = ft.AlertDialog(
            title=ft.Text('Login Failed', text_align=ft.TextAlign.CENTER),
            content=ft.Text('Invalid username or password', text_align=ft.TextAlign.CENTER),
            icon=ft.Icon(name=ft.Icons.ERROR, color='red'),
            actions=[ft.TextButton('OK', on_click=lambda e: close_dialog(failure_dialog))]
        )

        invalid_input_dialog = ft.AlertDialog(
            title=ft.Text('Input Error', text_align=ft.TextAlign.CENTER),
            content=ft.Text('Please enter username and password', text_align=ft.TextAlign.CENTER),
            icon=ft.Icon(name=ft.Icons.INFO, color='blue'),
            actions=[ft.TextButton('OK', on_click=lambda e: close_dialog(invalid_input_dialog))]
        )

        database_error_dialog = ft.AlertDialog(
            title=ft.Text('Database Error'),
            content=ft.Text('An error occurred while connecting to the database'),
            actions=[ft.TextButton('OK', on_click=lambda e: close_dialog(database_error_dialog))]
        )

        # if username or password is empty, open the invalid input dialog
        if not username or not password:
            page.open(invalid_input_dialog)
            return

        try:
            connection = connect_db()
            cursor = connection.cursor()

            cursor.execute('SELECT * FROM user WHERE username = %s AND password = %s', (username, password))
            result = cursor.fetchone()
            connection.close()

            # open success dialog if there is a result, else open the failure dialog
            page.open(success_dialog) if result else page.open(failure_dialog)
            page.update()

        except Error:
            # open database error dialog if the there's an error while connecting to the database
            page.open(database_error_dialog)
            page.update()

    # a function that close a dialog when 'OK' was clicked
    def close_dialog(dialog):
        dialog.open = False
        page.update()


    # login button
    login_button = ft.ElevatedButton(
        text='Login',
        on_click=login_click,
        bgcolor='white',
        width=100,
        icon=ft.Icons.LOGIN,
    )

    #  container holding the username and password field
    field_container = ft.Container(
        content=ft.Column([
            username_field, password_field
        ], spacing=20)
    )

    # container holding the login button
    button_container = ft.Container(
        content=login_button,
        alignment=ft.alignment.top_right,
        margin=ft.margin.only(0,20,40,0)
    )

    # adds all the elements into the page
    page.add(login_title, field_container, button_container)


ft.app(target=main)
