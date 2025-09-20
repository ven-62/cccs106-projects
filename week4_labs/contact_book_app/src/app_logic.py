# app_logic.py
import flet as ft
from database import update_contact_db, delete_contact_db, add_contact_db, get_all_contacts_db


def display_contacts(page, contacts_list_view, db_conn, searching=None):
    """Fetches and displays all and searched contacts in the ListView."""
    contacts_list_view.controls.clear()
    contacts = get_all_contacts_db(db_conn, searching)

    for contact in contacts:
        contact_id, name, phone, email = contact

        contacts_list_view.controls.append(
            ft.Card(
                ft.ListTile(
                    title=ft.Text(name, weight=ft.FontWeight.W_600),
                    subtitle=ft.Column([
                        ft.Row([
                            ft.Icon(name=ft.Icons.PHONE, size=20),
                            ft.Text(phone if phone else '-')
                        ]),
                        ft.Row([
                            ft.Icon(name=ft.Icons.EMAIL, size=20),
                            ft.Text(email if email else '-')    
                        ])
                    ], spacing=1),
                    trailing=ft.PopupMenuButton(
                        icon=ft.Icons.MORE_VERT,
                        items=[
                            ft.PopupMenuItem(
                                text="Edit",
                                icon=ft.Icons.EDIT,
                                on_click=lambda _, c=contact: open_edit_dialog(page, c,
                                db_conn, contacts_list_view)
                            ),
                            ft.PopupMenuItem(),
                            ft.PopupMenuItem(
                                text="Delete",
                                icon=ft.Icons.DELETE,
                                on_click=lambda  _, cid=contact_id: open_delete_dialog(page, cid, db_conn, contacts_list_view)
                            )
                        ]
                    )
                ), is_semantic_container=True
            )
        )
    page.update()

def add_contact(page, inputs, contacts_list_view, db_conn):
    """Adds a new contact and refreshes the list."""
    name_input, phone_input, email_input = inputs
    name = name_input.value
    phone = phone_input.value
    email = email_input.value

    if not name:
        # Input valiadtion (if name field is empty, throws an error text)
        name_input.error_text = 'Name cannot be empty'
        
    else:
        name_input.error_text = None
        add_contact_db(db_conn, name, phone, email)

        for field in inputs:
            field.value = ""

        display_contacts(page, contacts_list_view, db_conn)

    page.update()

def delete_contact(page, contact_id, db_conn, contacts_list_view, dialog):
    """Deletes a contact and refreshes the list."""
    delete_contact_db(db_conn, contact_id)
    display_contacts(page, contacts_list_view, db_conn)

    page.close(dialog)

def edit_contact(page, dialog, db_conn, cid, textfields, contacts_list_view):
    'Edit a contact and refreshes the list'
    name_field, phone_field, email_field = textfields
    name_value = name_field.value

    if not name_value:
        # Thorws an error text if the name text field is empty
        name_field.error_text = 'Name cannot be empty'
    
    else:
        update_contact_db(db_conn, cid, name_value, phone_field.value, email_field.value)
        display_contacts(page, contacts_list_view, db_conn)

        page.close(dialog)

    page.update()

def open_edit_dialog(page, contact, db_conn, contacts_list_view):
    """Opens a dialog to edit a contact's details."""
    contact_id, name, phone, email = contact

    border_color = ft.Colors.WHITE if page.theme_mode is ft.ThemeMode.DARK else ft.Colors.BLACK

    edit_name = ft.TextField(
        label="Name",
        value=name,
        width=350,
        focused_border_color=ft.Colors.PRIMARY,
        border_color=border_color,
        on_change=lambda _: no_error_text(page, edit_name)
    )
    edit_phone = ft.TextField(
        label="Phone",
        value=phone,
        width=350,
        focused_border_color=ft.Colors.PRIMARY,
        border_color=border_color
    )
    edit_email = ft.TextField(
        label="Email",
        value=email,
        width=350,
        focused_border_color=ft.Colors.PRIMARY,
        border_color=border_color
    )

    dialog_textfields = (edit_name, edit_phone, edit_email)

    edit_dialog = ft.AlertDialog(
        title=ft.Text('Edit contact'),
        content=ft.Container(
            content=ft.Column(
                [edit_name, edit_phone, edit_email]
            ), 
            height=190,
            width=350
        ),
        actions=[
            ft.TextButton(
                'CANCEL', width=90,
                on_click=lambda e: page.close(edit_dialog)
            ),
            ft.FilledButton(
                'DONE', width=90,
                on_click=lambda _: edit_contact(
                    page,
                    edit_dialog,
                    db_conn,
                    contact_id,
                    dialog_textfields,
                    contacts_list_view
                )
            )
        ]
    )
    page.open(edit_dialog)
    page.update()

def open_delete_dialog(page, contact_id, db_conn, contacts_list_view):
    '''Opens a dialog to delete a specific contact'''
    delete_dialog = ft.AlertDialog(
        title=ft.Text('Delete'),
        content=ft.Text('Are you sure you want to delete this contact?'),
        actions=[
            ft.TextButton(
                'NO', width=80,
                on_click=lambda e: page.close(delete_dialog)
            ),
            ft.FilledButton(
                'YES', width=80,
                on_click=lambda _, cid=contact_id: delete_contact(page, cid, db_conn, contacts_list_view, delete_dialog)
            )
        ]
    )
    page.open(delete_dialog)

def toggle_theme(page, button, textfields):
    '''Toggles theme mode of the page'''
    if page.theme_mode is ft.ThemeMode.DARK:
        page.theme_mode = ft.ThemeMode.LIGHT
        button.icon = ft.Icons.LIGHT_MODE

        for tf in textfields:
            tf.border_color = ft.Colors.BLACK

    else:
        page.theme_mode = ft.ThemeMode.DARK
        button.icon = ft.Icons.DARK_MODE

        for tf in textfields:
            tf.border_color = ft.Colors.WHITE

    page.update()

def no_error_text(page, textfield):
    textfield.error_text = None
    page.update()
