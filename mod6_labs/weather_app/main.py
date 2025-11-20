"""Weather Application using Flet v0.28.3"""

import flet as ft
from weather_service import WeatherService
from config import Config
from pathlib import Path
import json
import datetime
import asyncio


class WeatherApp:
    """Main Weather Application class."""
    
    def __init__(self, page: ft.Page):
        self.page = page
        self.weather_service = WeatherService()

        # Search history
        self.history_file = Path("search_history.json")
        self.search_history = self.load_history()[:5]

        self.setup_page()
        self.build_ui()

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
        self.page.window.width = Config.APP_WIDTH
        self.page.window.height = Config.APP_HEIGHT
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
            icon=ft.Icons.MIC
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
            on_focus=self.show_history,
            on_blur=self.hide_history,
        )

        # Search history
        self.history_dropdown = ft.Container(
            content=ft.Column(spacing=5),
            visible=True,
            border_radius=2,
            padding=10,
            # shadow=ft.BoxShadow(blur_radius=1)
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
            visible=False
        )
        
        # Error message
        self.error_message = ft.Text(
            "",
            color=ft.Colors.RED_700,
            visible=False,
        )

        # Update the Column to include the theme button in the title row
        title_row = ft.Row(
            [
                self.title,
                self.theme_button,
            ],
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
        )

        search_row = ft.Column(
            controls=[
                ft.Row(
                    [
                        self.city_input,
                        self.search_button
                    ]
                )
            ],
            expand=True
        )

        content_row = ft.Container(
            content=ft.Row(
                [
                    self.weather_container,
                    self.forecast_container
                ],
                expand=True,
                spacing=20,
                alignment=ft.MainAxisAlignment.CENTER
            )
        )
                
        # Loading indicator
        self.loading = ft.ProgressRing(visible=False)

        self.update_theme_icon()
        
        # Add all components to page
        self.page.add(
            ft.Stack(
                controls=[
                    # MAIN PAGE CONTENT
                    ft.Column(
                        [
                            title_row,
                            ft.Divider(height=20, color=ft.Colors.TRANSPARENT),
                            search_row,
                            ft.Divider(height=20, color=ft.Colors.TRANSPARENT),
                            self.loading,
                            self.error_message,
                            content_row,
                        ],
                        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                        spacing=10,
                    ),
                    # FLOATING DROPDOWN
                    ft.Container(
                        top=137,   # Position relative to entire page
                        left=40,
                        right=50,
                        content=self.history_dropdown
                    ),
                ]
            )
        )


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
                return json.load(f)
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

        self.update_theme_icon()
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
                    color=ft.Colors.GREY_700,
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
            controls=[self.create_forecast_card(current_date.strftime('%A').upper(), self.icon_code, self.temp, self.humidity, self.wind_speed, self.pressure, self.cloudiness)],
            expand=2,spacing=10
        )

        for i in range(1, 5):
            next_day = current_date + datetime.timedelta(days=i)

            icon_code = forecast_days[i].get("weather", [{}])[0].get("icon", "01d")
            temperature = forecast_days[i].get("main", {}).get("temp", 0)
            humidity = forecast_days[i].get("main", {}).get("humidity", 0)
            wind_speed = forecast_days[i].get("wind", {}).get("speed", 0)
            pressure = forecast_days[i].get("main",{}).get("pressure", 0)
            cloudiness = forecast_days[i].get("clouds",{}).get("all", 0)

            self.days_container.controls.append(
                self.create_forecast_card(
                    next_day.strftime('%A').upper(),
                    icon_code,
                    temperature,
                    humidity,
                    wind_speed,
                    pressure,
                    cloudiness)
            )

        # Build forecast display
        self.forecast_container.content = ft.Column(
            [
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
     
    
    def create_forecast_card(self, day, icon_code, temp, humidity, wind_speed, pressure, cloudiness):
        def create_info_row(icon, value):
            return ft.Row(
                [
                    ft.Icon(icon, size=20, color=ft.Colors.BLUE_500),
                    ft.Text(
                        value,
                        size=12,
                        weight=ft.FontWeight.BOLD,
                        color=ft.Colors.BLUE_900,
                    )
                ]
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
                                ft.Icons.WATER_DROP, f"{humidity}%"
                            ),
                            create_info_row(
                                ft.Icons.AIR, f"{wind_speed} m/s"
                            ),
                            create_info_row(
                                ft.Icons.COMPRESS, f"{pressure} hPa"
                            ),
                            create_info_row(
                                ft.Icons.CLOUD, f"{cloudiness}%"
                            )
                        ],
                        spacing=10,
                        alignment=ft.CrossAxisAlignment.CENTER

                    )
                ],
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=20
            ),
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
    
    def update_theme_icon(self):
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
        self.page.update()


def main(page: ft.Page):
    """Main entry point."""
    WeatherApp(page)


if __name__ == "__main__":
    ft.app(target=main)