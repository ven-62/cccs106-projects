"""Weather Application using Flet v0.28.3"""

import flet as ft
from weather_service import WeatherService
from config import Config
from pathlib import Path
import json
import datetime
import asyncio
import speech_recognition as sr
import threading
import winsound
import time

class WeatherApp:
    """Main Weather Application class."""
    
    def __init__(self, page: ft.Page):
        self.page = page
        self.weather_service = WeatherService()

        # Search history
        self.history_file = Path("search_history.json")
        self.search_history = self.load_history()

        self.cities_file = Path("cities.json")
        self.saved_cities = self.load_cities()

        self.setup_page()
        self.build_ui()

        self.recognizer = sr.Recognizer()
        self.mic_stream = None
        self.listening = False

    def setup_page(self):
        """Configure page settings."""
        self.page.title = Config.APP_TITLE
        
        # Add theme switcher
        self.page.theme_mode = ft.ThemeMode.SYSTEM  # Use system theme
        
        # Custom theme Colors
        self.page.theme = ft.Theme(
            color_scheme_seed=ft.Colors.BLUE,
        )
        
        self.page.padding = 20
        
        # Window properties are accessed via page.window object in Flet 0.28.3
        self.page.window.maximized = True
        self.page.window.resizable = False
        self.page.window.center()
    
    def build_ui(self):
        """Build the user interface."""
        # Title
        self.title = ft.Text(
            "Weather App",
            size=32,
            weight=ft.FontWeight.BOLD,
            color=ft.Colors.BLUE_700,
        )
        
        # Theme toggle button
        self.theme_button = ft.IconButton(
            icon=ft.Icons.DARK_MODE,
            tooltip="Toggle theme",
            on_click=self.toggle_theme,
        )

        # Microphone search button
        self.mic_button = ft.IconButton(
            icon=ft.Icons.MIC,
            on_click=self.mic_click
        )

        # City input field
        self.city_input = ft.TextField(
            label="Enter city name",
            hint_text="e.g., London, Tokyo, New York",
            border_color=ft.Colors.BLUE_400,
            icon=ft.Icons.LOCATION_CITY,
            suffix_icon=self.mic_button,
            autofocus=True,
            expand=True,
            on_submit=self.on_search,
            on_change=self.show_history,
            on_blur=self.hide_history,
        )

        self.live_text = ft.Text("Say something...", size=16)

        self.done_button = ft.TextButton("Done", on_click=self.stop_listening)

        self.listening_dialog = ft.AlertDialog(
            modal=True,
            content=ft.Column(
                [
                    ft.Text("Listening...", size=20, weight="bold"),
                    ft.Container(height=10),
                    self.live_text
                ],
                tight=True,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER),
            actions=[self.done_button],
            actions_alignment=ft.MainAxisAlignment.CENTER,
        )

        # Search history
        self.history_dropdown = ft.Container(
            content=ft.Column(spacing=5),
            visible=False,
            border_radius=2,
            padding=10,
        )
        
        # Search button
        self.search_button = ft.IconButton(
            icon=ft.Icons.SEARCH,
            on_click=self.on_search
        )

        self.temperature_text = ft.Text()
        
        # Weather display container
        self.weather_container = ft.Container(
            bgcolor=ft.Colors.BLUE_50,
            border_radius=10,
            padding=20,
            visible=False
        )

        # Forecast display container
        self.forecast_container = ft.Container(
            bgcolor=ft.Colors.BLUE_50,
            border_radius=10,
            padding=20,
            visible=False,
        )
        
        # Error message
        self.error_message = ft.Text(
            "",
            color=ft.Colors.RED_700,
            visible=False,
            # text_align=ft.TextAlign.CENTER
        )
        
        self.cities_column = ft.Column(
            spacing=6,
            scroll=ft.ScrollMode.ALWAYS
        )

        self.cities_container = ft.Container(
            content=self.cities_column,
            border_radius=10,
            padding=10,
            height=167,
            width=680,
            bgcolor=ft.Colors.WHITE
        )

        # Update the Column to include the theme button in the title row
        title_row = ft.Row(
            [
                self.title,
                self.theme_button,
            ],
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
        )

        # Search row with search input and search button
        search_row = ft.Column(
            controls=[
                ft.Row(
                    [
                        self.city_input,
                        self.search_button
                    ]
                )
            ],
            
        )

        # Container for all the content
        content_row = ft.Container(
            content=ft.Row(
                [
                    self.weather_container,
                    self.forecast_container
                ],
                spacing=20,
                alignment=ft.MainAxisAlignment.CENTER
            )
        )
                
        
        # Loading indicator
        self.loading = ft.ProgressRing(visible=False)

        self.update_theme_colors()

        # Add all components to page
        self.page.add(
            ft.Stack(
                controls=[
                    ft.Container(
                        content=ft.Column(
                            [
                                self.loading,
                                self.error_message
                            ],
                            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                            spacing=10,
                        ),
                        alignment=ft.alignment.center,
                        top=200,
                        right=20,
                        left=20
                    ),
                    # MAIN PAGE CONTENT
                    ft.Column(
                        [
                            title_row,
                            ft.Divider(height=20, color=ft.Colors.TRANSPARENT),
                            search_row,
                            ft.Divider(height=20, color=ft.Colors.TRANSPARENT),
                            content_row,
                        ],
                        horizontal_alignment=ft.CrossAxisAlignment.START,
                        spacing=10,
                    ),
                    # FLOATING DROPDOWN
                    ft.Container(
                        top=137,
                        left=40,
                        right=50,
                        content=self.history_dropdown
                    ),
                    self.listening_dialog
                ],
                expand=True
            )
        )
    
    def load_cities(self):
        """Load saved cities from JSON file."""
        if self.cities_file.exists():
            with open(self.cities_file, "r") as f:
                try:
                    return json.load(f)
                except json.JSONDecodeError:
                    return []
        return []

    async def load_saved_city_cards(self):
        """Fetch weather for saved cities and add cards to UI."""
        for city in self.saved_cities:
            try:
                data = await self.weather_service.get_weather(city)
                temp = data["main"]["temp"]
                desc = data["weather"][0]["description"].title()
                self.add_city_card(city, temp, desc)
            except Exception as e:
                print(f"Failed to load {city}: {e}")

    def add_city_card(self, city_name: str, temp: float = None, desc: str = None):
        card = ft.Container(
            padding=10,
            border_radius=8,
            bgcolor=ft.colors.WHITE,
            shadow=ft.BoxShadow(
                spread_radius=1,
                blur_radius=3,
                color=ft.colors.with_opacity(0.15, ft.colors.BLACK),
            ),
            content=ft.Row(
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                controls=[
                    ft.Column(
                        spacing=2,
                        controls=[
                            ft.Text(city_name, size=16, weight=ft.FontWeight.BOLD),
                            ft.Text(
                                f"{temp}°C • {desc}" if temp and desc else "",
                                size=12,
                                color=ft.colors.GREY_700
                            ),
                        ]
                    ),
                    ft.IconButton(
                        icon=ft.icons.DELETE,
                        icon_size=20,
                        on_click=lambda e: self.remove_city(city_name, card),
                    )
                ]
            )
        )

        self.cities_column.controls.append(card)
        self.page.update()

    def remove_city(self, city_name: str, card):
        # Remove from UI
        self.cities_column.controls.remove(card)
        self.page.update()

        # Remove from JSON
        if city_name in self.saved_cities:
            self.saved_cities.remove(city_name)
            self.save_cities()

    def open_add_city_dialog(self, e):
        # Text input for city
        self.city_input_dialog = ft.TextField(
            label="Enter city name",
            autofocus=True,
            hint_text="e.g., Manila"
        )

        # Dialog setup
        self.add_city_dialog = ft.AlertDialog(
            modal=True,
            title=ft.Text("Add City"),
            content=self.city_input_dialog,
            actions=[
                ft.TextButton(
                    "Cancel",
                    on_click=lambda e: self.close_dialog()
                ),
                ft.TextButton(
                    "Add",
                    on_click=lambda e: asyncio.create_task(self.add_city_from_dialog())
                ),
            ]
        )

        self.page.dialog = self.add_city_dialog
        self.add_city_dialog.open = True
        self.page.update()

    def close_dialog(self):
        self.add_city_dialog.open = False
        self.page.update()

    async def add_city_from_dialog(self):
        city = self.city_input_dialog.value.strip()
        if not city:
            return

        # Fetch weather data (your existing method)
        try:
            data = await self.weather_service.get_weather(city)
            temp = data["main"]["temp"]
            desc = data["weather"][0]["description"].title()
        except Exception as e:
            # Show error message if city not found
            self.page.snack_bar = ft.SnackBar(ft.Text(f"Error: {e}"))
            self.page.snack_bar.open = True
            self.page.update()
            return

        # Add city card to UI
        self.add_city_card(city, temp, desc)

        # Save to JSON
        if city not in self.saved_cities:
            self.saved_cities.append(city)
            self.save_cities()

        # Close dialog
        self.close_dialog()






    def show_history(self, e):
        # Do NOT show dropdown if history is empty
        if not self.search_history:
            self.history_dropdown.visible = False
            self.page.update()
            return
        
        # Show normally
        self.update_history_list()
        self.history_dropdown.visible = True
        self.page.update()

    def hide_history(self, e):
        # Small delay so clicking history doesn't instantly hide
        import time
        time.sleep(0.1)
        self.history_dropdown.visible = False
        self.page.update()

    def update_history_list(self):
        self.history_dropdown.content.controls.clear()

        for city in self.search_history:
            self.history_dropdown.content.controls.append(
                ft.ListTile(
                    title=ft.Text(city),
                    on_click=lambda e, c=city: self.select_history(c),
                    trailing=ft.IconButton(
                        icon=ft.Icons.CLOSE,
                        data=city,
                        on_click=self.remove_from_history
                    )
                )
            )

    def select_history(self, city):
        self.city_input.value = city
        self.history_dropdown.visible = False
        self.page.update()
        self.on_search(None)

    def remove_from_history(self, e):
        city = e.control.data
        if city in self.search_history:
            self.search_history.remove(city)
            self.save_history()
            self.update_history_list()
            self.page.update()

    def load_history(self):
        """Load search history from file."""
        if self.history_file.exists():
            with open(self.history_file, 'r') as f:
                return json.load(f)[:5]
        return []
    
    def save_history(self):
        """Save search history to file."""
        with open(self.history_file, 'w') as f:
            json.dump(self.search_history, f)
    
    def add_to_history(self, city: str):
        """Add city to history."""
        if city not in self.search_history:
            self.search_history.insert(0, city)
            self.search_history = self.search_history[:10]  # Keep only 10
            self.save_history()

        # Refresh the dropdown UI
        self.update_history_list()

    def callback(self, recognizer, audio):
        if not self.listening:
            return

        try:
            text = recognizer.recognize_google(audio)
            self.live_text.value = text.title()
            self.page.update()

            # Stop listening immediately after first recognition
            self.listening = False
            if self.mic_stream:
                self.mic_stream(wait_for_stop=False)
                self.mic_stream = None

            # Play end sound
            winsound.PlaySound(Config.END_SOUND, winsound.SND_FILENAME | winsound.SND_ASYNC)

            self.city_input.value = self.live_text.value
            time.sleep(2) # Delay for 2 seconds
            self.listening_dialog.open = False

            self.page.update()
            self.get_weather()

        except sr.UnknownValueError:
            pass  # ignore noise
        except Exception as e:
            self.live_text.value = f"Error: {e}"
            self.page.update()

    def mic_click(self, e):
        self.listening = True
        self.live_text.value = "Say something..."
        self.listening_dialog.open = True
        self.page.update()

        # Play start sound
        winsound.PlaySound(Config.START_SOUND, winsound.SND_FILENAME | winsound.SND_ASYNC)

        # Start background listening
        def start_listening():
            mic = sr.Microphone()
            # self.recognizer.adjust_for_ambient_noise(mic)
            self.mic_stream = self.recognizer.listen_in_background(mic, self.callback)


        threading.Thread(target=start_listening, daemon=True).start()

    def stop_listening(self, e):
        self.listening = False
        temp_text = self.city_input.value

        if self.mic_stream:
            self.mic_stream(wait_for_stop=False)
            self.mic_stream = None

        if self.live_text.value == "Say something...":
            pass
        else:
            # Final recognized text → put into TextField
            self.city_input.value = self.live_text.value

        self.listening_dialog.open = False
        self.page.update()

    def toggle_theme(self, e):
        """Toggle between light and dark theme correctly, with instant icon update."""

        current_mode = self.page.theme_mode

        # Determine actual brightness if using SYSTEM
        if current_mode == ft.ThemeMode.SYSTEM:
            is_light = self.page.platform_brightness == ft.Brightness.LIGHT
        else:
            is_light = current_mode == ft.ThemeMode.LIGHT

        # Toggle logic
        if is_light:
            self.page.theme_mode = ft.ThemeMode.DARK
        else:
            self.page.theme_mode = ft.ThemeMode.LIGHT

        self.update_theme_colors()
        self.page.update()
    
    def on_search(self, e):
        """Handle search button click or enter key press."""
        self.page.run_task(self.get_weather)
    
    async def get_weather(self):
        """Fetch and display weather data."""
        city = self.city_input.value.strip()
        
        # Validate input
        if not city:
            self.show_error("Please enter a city name")
            return
        
        # Show loading, hide previous results
        self.add_to_history(city)
        self.loading.visible = True
        self.error_message.visible = False
        self.weather_container.visible = False
        self.forecast_container.visible = False
        self.page.update()
        
        try:
            # Fetch weather data and forecast
            weather_data = await self.weather_service.get_weather(city)
            forecast_data = await self.weather_service.get_forecast(city)
            
            # Display weather and forecast
            await self.display_weather(weather_data)
            await self.display_forecast(forecast_data)
            
        except Exception as e:
            self.show_error(str(e))
        
        finally:
            self.loading.visible = False
            self.page.update()
    
    async def display_weather(self, data: dict):
        """Display weather information."""
        # Extract data
        city_name = data.get("name", "Unknown")
        country = data.get("sys", {}).get("country", "")
        feels_like = data.get("main", {}).get("feels_like", 0)
        description = data.get("weather", [{}])[0].get("description", "").title()

        self.temp = data.get("main", {}).get("temp", 0)
        self.icon_code = data.get("weather", [{}])[0].get("icon", "01d")

        self.humidity = data.get("main", {}).get("humidity", 0)
        self.wind_speed = data.get("wind", {}).get("speed", 0)
        self.pressure = data.get("main",{}).get("pressure", 0)
        self.cloudiness = data.get("clouds",{}).get("all", 0)

        self.min_temp = data.get("main", {}).get("temp_min", 0)
        self.max_temp = data.get("main", {}).get("temp_max", 0)

        self.temperature_text = ft.Text(
            f"{self.temp:.1f}°C",
            size=48,
            weight=ft.FontWeight.BOLD,
            color=ft.Colors.BLUE_900 if self.page.platform_brightness == ft.Brightness.LIGHT else ft.Colors.BLUE_50,
        )

        # Build weather display
        self.weather_container.content = ft.Column(
            [
                # Location
                ft.Text(
                    f"{city_name}, {country}",
                    size=24,
                    weight=ft.FontWeight.BOLD,
                ),
                
                # Weather icon and description
            
                ft.Image(
                    src=f"https://openweathermap.org/img/wn/{self.icon_code}@2x.png",
                    width=100,
                    height=100,
                ),
                ft.Text(
                    description,
                    size=20,
                    italic=True,
                ),
                
                self.temperature_text,
                
                ft.Text(
                    f"Feels like {feels_like:.1f}°C",
                    size=16,
                ),

                ft.Row(
                    [
                        ft.Row(
                            [
                                ft.Icon(ft.Icons.ARROW_DOWNWARD, size=14),
                                ft.Text(f"{self.min_temp:.1f}°C", size=14)
                            ],
                            spacing=3
                        ),
                        ft.Row(
                            [
                                ft.Icon(ft.Icons.ARROW_UPWARD, size=14),
                                ft.Text(f"{self.max_temp:.1f}°C", size=14)
                            ],
                            spacing=3
                        )
                    ],
                    spacing=10
                ),
                
                ft.Divider(),
                
                # Additional info
                ft.Row(
                    [
                        self.create_info_card(
                            ft.Icons.WATER_DROP,
                            "Humidity",
                            f"{self.humidity}%"
                        ),
                        self.create_info_card(
                            ft.Icons.AIR,
                            "Wind Speed",
                            f"{self.wind_speed} m/s"
                        )
                    ],
                    expand=2,
                    alignment=ft.MainAxisAlignment.CENTER,
                ),
                ft.Row(
                    [
                        self.create_info_card(
                            ft.Icons.COMPRESS,
                            "Pressure",
                            f"{self.pressure} hPa"
                        ),
                        self.create_info_card(
                            ft.Icons.CLOUD,
                            "Cloudiness",
                            f"{self.cloudiness}%"
                        )
                    ],
                    expand=True,
                    alignment=ft.MainAxisAlignment.CENTER
                )
            ],
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=7
        )

        # Animation
        self.weather_container.animate_opacity = 300
        self.weather_container.opacity = 0
        self.weather_container.visible = True
        self.page.update()

        # Fade in
        await asyncio.sleep(0.1)
        self.weather_container.opacity = 1
        self.page.update()

    async def display_forecast(self, data):
        """Display five-day weather forecast"""
        # Extract data
        forecast_days = data.get("list", {})
       
        current_date = datetime.date.today()

        self.days_container = ft.Row(
            controls=[
                self.create_forecast_card(
                    current_date.strftime('%A').upper(),
                    self.icon_code,
                    self.temp,
                    self.min_temp,
                    self.max_temp)
                ],
            expand=True,
            spacing=10
        )

        for i in range(1, 5):
            next_day = current_date + datetime.timedelta(days=i)

            icon_code = forecast_days[i].get("weather", [{}])[0].get("icon", "01d")
            temperature = forecast_days[i].get("main", {}).get("temp", 0)
            min_temp = forecast_days[i].get("main", {}).get("temp_min", 0)
            max_temp = forecast_days[i].get("main", {}).get("temp_max", 0)

            self.days_container.controls.append(
                self.create_forecast_card(
                    next_day.strftime('%A').upper(),
                    icon_code,
                    temperature,
                    min_temp,
                    max_temp
                )
            )

        # Build forecast display
        self.forecast_container.content = ft.Column(
            [
                ft.Row(
                    [
                        ft.Text("Multi-City Overview", size=24, weight=ft.FontWeight.BOLD),
                        ft.IconButton(
                            icon=ft.Icons.ADD,
                            tooltip="Add City",
                            on_click=self.open_add_city_dialog
                        )
                    ],
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                ),  
                self.cities_container,
                ft.Text(
                    "5-Day Forecast",
                    size=24,
                    weight=ft.FontWeight.BOLD,
                ),
                ft.Divider(),
                self.days_container
            ]
        )

        # Animation
        self.forecast_container.animate_opacity = 300
        self.forecast_container.opacity = 0
        self.forecast_container.visible = True
        self.page.update()

        # Fade in
        await asyncio.sleep(0.1)
        self.forecast_container.opacity = 1
        self.page.update()

    def create_forecast_card(self, day, icon_code, temp, min_temp, max_temp):
        def create_info_row(icon, value):
            return ft.Row(
                [
                    ft.Icon(icon, size=14, color=ft.Colors.BLUE_500),
                    ft.Text(
                        value,
                        size=12,
                        weight=ft.FontWeight.BOLD,
                        color=ft.Colors.BLUE_900,
                    )
                ],
                expand=True,
                alignment=ft.MainAxisAlignment.CENTER
            )
        
        return ft.Container(
            content=ft.Column(
                [
                    ft.Text(day, color=ft.Colors.BLACK, weight=ft.FontWeight.W_500),
                    ft.Image(
                        src=f"https://openweathermap.org/img/wn/{icon_code}@2x.png",
                        width=80,
                        height=80,
                    ),
                    ft.Text(
                        f"{temp:.1f}°C",
                        size=24,
                        weight=ft.FontWeight.W_500,
                        color=ft.Colors.BLUE_900,
                    ),
                    ft.Column(
                        [
                            create_info_row(
                                ft.Icons.ARROW_DOWNWARD, f"{min_temp:.1f}°C"
                            ),
                            create_info_row(
                                ft.Icons.ARROW_UPWARD, f"{max_temp:.1f}°C"
                            )
                        ],
                        spacing=10,
                        alignment=ft.MainAxisAlignment.CENTER
                    )
                ],
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=20,
                expand=True
            ),
            expand=True,
            bgcolor=ft.Colors.WHITE,
            border_radius=10,
            padding=15,
            width=130,
        )

    def create_info_card(self, icon, label, value):
        """Create an info card for weather details."""
        return ft.Container(
            content=ft.Column(
                [
                    ft.Icon(icon, size=30, color=ft.Colors.BLUE_700),
                    ft.Text(label, size=12, color=ft.Colors.GREY_600),
                    ft.Text(
                        value,
                        size=16,
                        weight=ft.FontWeight.BOLD,
                        color=ft.Colors.BLUE_900,
                    ),
                ],
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=5,
            ),
            bgcolor=ft.Colors.WHITE,
            border_radius=10,
            padding=15,
            width=150,
        )
    
    def update_theme_colors(self):
        # Determine actual brightness
        if self.page.theme_mode == ft.ThemeMode.SYSTEM:
            is_light = self.page.platform_brightness == ft.Brightness.LIGHT
        else:
            is_light = self.page.theme_mode == ft.ThemeMode.LIGHT

        # Assign icon based on brightness
        self.theme_button.icon = (
            ft.Icons.DARK_MODE if is_light else ft.Icons.LIGHT_MODE
        )
        self.weather_container.bgcolor = (
            ft.Colors.BLUE_50 if is_light else ft.Colors.BLUE_GREY_900
        )
        self.forecast_container.bgcolor = (
            ft.Colors.BLUE_50 if is_light else ft.Colors.BLUE_GREY_900
        )
        self.history_dropdown.bgcolor = (
            ft.Colors.WHITE if is_light else ft.Colors.BLUE_GREY_900
        )
        self.temperature_text.color = (
            ft.Colors.BLUE_900 if is_light else ft.Colors.BLUE_50
        )

    def show_error(self, message: str):
        """Display error message."""
        self.error_message.value = f"❌ {message}"
        self.error_message.visible = True
        self.weather_container.visible = False
        self.forecast_container.visible = False
        self.page.update()

def main(page: ft.Page):
    """Main entry point."""
    WeatherApp(page)

if __name__ == "__main__":
    ft.app(target=main)