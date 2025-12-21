package com.mycoder.rocketchat.ui.compose.theme

import android.app.Activity
import androidx.compose.foundation.isSystemInDarkTheme
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.darkColorScheme
import androidx.compose.material3.lightColorScheme
import androidx.compose.runtime.Composable
import androidx.compose.runtime.SideEffect
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.toArgb
import androidx.compose.ui.platform.LocalView
import androidx.core.view.WindowCompat

// MyCoder brand colors
private val MyCoder Blue = Color(0xFF1976D2)
private val MyCoderBlueLight = Color(0xFF63A4FF)
private val MyCoderBlueDark = Color(0xFF004BA0)
private val MyCoderOrange = Color(0xFFFF6F00)
private val MyCoderOrangeLight = Color(0xFFFFA040)
private val MyCoderOrangeDark = Color(0xFFC43E00)

private val LightColorScheme = lightColorScheme(
    primary = MyCoderBlue,
    onPrimary = Color.White,
    primaryContainer = MyCoderBlueLight,
    onPrimaryContainer = Color.Black,
    secondary = MyCoderOrange,
    onSecondary = Color.White,
    secondaryContainer = MyCoderOrangeLight,
    onSecondaryContainer = Color.Black,
    background = Color(0xFFF5F5F5),
    surface = Color.White,
    error = Color(0xFFB00020)
)

private val DarkColorScheme = darkColorScheme(
    primary = MyCoderBlueLight,
    onPrimary = Color.Black,
    primaryContainer = MyCoderBlueDark,
    onPrimaryContainer = Color.White,
    secondary = MyCoderOrangeLight,
    onSecondary = Color.Black,
    secondaryContainer = MyCoderOrangeDark,
    onSecondaryContainer = Color.White,
    background = Color(0xFF121212),
    surface = Color(0xFF1E1E1E),
    error = Color(0xFFCF6679)
)

@Composable
fun MyCoderTheme(
    darkTheme: Boolean = isSystemInDarkTheme(),
    content: @Composable () -> Unit
) {
    val colorScheme = if (darkTheme) DarkColorScheme else LightColorScheme

    val view = LocalView.current
    if (!view.isInEditMode) {
        SideEffect {
            val window = (view.context as Activity).window
            window.statusBarColor = colorScheme.primary.toArgb()
            WindowCompat.getInsetsController(window, view).isAppearanceLightStatusBars = !darkTheme
        }
    }

    MaterialTheme(
        colorScheme = colorScheme,
        typography = Typography,
        content = content
    )
}
