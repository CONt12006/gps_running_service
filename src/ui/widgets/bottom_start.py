from kivy.graphics import Color, RoundedRectangle
from kivy.metrics import dp
from kivy.uix.button import Button


class BottomStart(Button):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.text = "Начать"                    # Текст на кнопке
        self.font_size = dp(22)                 # Размер шрифта текста на кнопке
        self.color = (1, 1, 1, 1)               # Цвет шрифта
        self.background_normal = ""             # Это фон кнопки в обычном состоянии(его надо убрать чтобы создать свой, тк моя кнопка будет создана через RoundedRectangle)
        self.background_down = ""               # Это фон кнопки в нажатом состоянии
        self.background_color = (0, 0, 0, 0)    # Стандартный фон делается полностью прозрачным
        self.size_hint = (0.65, None)
        self.height = dp(64)

        with self.canvas.before:
            # Зеленый цвет кнопки
            self.background_color_instruction = Color(
                0.0,
                0.82,
                0.32,
                1,
            )

            self.background_rectangle = RoundedRectangle(
                pos=self.pos,
                size=self.size,
                radius=[dp(16)],
            )
        self.bind(
            pos=self._update_background,
            size=self._update_background,
        )

    def _update_background(self, *args) -> None:
        self.background_rectangle.pos = self.pos
        self.background_rectangle.size = self.size

        """тут фукнция для bind на начала выдача gps"""