package com.sona.ai.motion

import androidx.compose.animation.EnterTransition
import androidx.compose.animation.ExitTransition
import androidx.compose.animation.core.tween
import androidx.compose.animation.fadeIn
import androidx.compose.animation.fadeOut
import androidx.compose.animation.slideInHorizontally
import androidx.compose.animation.slideOutHorizontally

object SonaTransitions {

    val enterTransition: EnterTransition =
        fadeIn(animationSpec = tween(300)) +
            slideInHorizontally(animationSpec = tween(300)) { it / 4 }

    val exitTransition: ExitTransition =
        fadeOut(animationSpec = tween(200)) +
            slideOutHorizontally(animationSpec = tween(200)) { -it / 4 }

    val popEnterTransition: EnterTransition =
        fadeIn(animationSpec = tween(300)) +
            slideInHorizontally(animationSpec = tween(300)) { -it / 4 }

    val popExitTransition: ExitTransition =
        fadeOut(animationSpec = tween(200)) +
            slideOutHorizontally(animationSpec = tween(200)) { it / 4 }
}
