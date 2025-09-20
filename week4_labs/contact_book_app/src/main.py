# main.py
import flet as ft
from database import init_db
from app_logic import *


def main(page: ft.Page):
    page.title = "Contact Book"
    page.vertical_alignment = ft.MainAxisAlignment.START
    page.horizontal_alignment = ft.CrossAxisAlignment.CENTER
    page.window_width = 400
    page.window_height = 600
    page.theme_mode = ft.ThemeMode.LIGHT
    
    db_conn = init_db()

    # name, phone, and email text fields
    name_input = ft.TextField(
        label="Name", width=350, focused_border_color=ft.Colors.PRIMARY,
        on_change=lambda _: no_error_text(page, name_input))
    phone_input = ft.TextField(label="Phone", width=350, focused_border_color=ft.Colors.PRIMARY)
    email_input = ft.TextField(label="Email", width=350, focused_border_color=ft.Colors.PRIMARY)

    inputs = (name_input, phone_input, email_input)

    # Holds all the contacts card
    contacts_list_view = ft.ListView(expand=3, spacing=0.5)

    # Button to add contact
    add_button = ft.ElevatedButton(
        text="Add Contact",
        width=135,
        icon=ft.Icons.ADD,
        on_click=lambda e: add_contact(page, inputs, contacts_list_view, db_conn)
    )

    # Search text field
    search_field = ft.TextField(
        hint_text='Search',
        width=350,
        focused_border_color=ft.Colors.PRIMARY,
        prefix_icon=ft.Icons.SEARCH,
        on_change=lambda _: display_contacts(
            page, contacts_list_view, db_conn, searching=search_field.value)
    )

    text_fields = list(inputs)
    text_fields.append(search_field)    

    # Toggle theme button
    theme_toggle_button = ft.IconButton(
        icon=ft.Icons.LIGHT_MODE,
        tooltip='Switch theme mode',
        on_click=lambda _: toggle_theme(page, theme_toggle_button, text_fields)
    )

    # Container that holds the field title and theme toggle icon button
    theme_btn_container = ft.SafeArea(
        content=ft.Row([
            ft.Text("Enter Contact Details:", size=20, weight=ft.FontWeight.BOLD),
            theme_toggle_button
        ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN
        ), width=350
    )

    # Container that holds the input text fields
    field_container = ft.Container(
        content=ft.Column([
            name_input,
            phone_input,
            email_input
        ]),
        width=350
    )

    # Container that holds the contact title and search field
    text_search_container = ft.Container(
        content=ft.Column([
            ft.Text("Contacts:", size=20, weight=ft.FontWeight.BOLD),
            search_field
        ]), width=350
    )

    # A Row holding the contact list view which displays all the contacts
    contacts_container = ft.Row(
        [contacts_list_view],
        expand=True,
        width=350,
        vertical_alignment=ft.CrossAxisAlignment.START
    )

    page.add(
        theme_btn_container,
        field_container,
        add_button,
        ft.Divider(),
        text_search_container,
        contacts_container
    )

    display_contacts(page, contacts_list_view, db_conn)


if __name__ == "__main__":
    ft.app(target=main)