package com.sona.ai.features.voice.bluetooth

import android.bluetooth.BluetoothAdapter
import android.content.Context
import android.media.AudioManager
import dagger.hilt.android.qualifiers.ApplicationContext
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import javax.inject.Inject
import javax.inject.Singleton

/**
 * Manages Bluetooth audio connections for the voice assistant.
 * Handles Bluetooth SCO (Synchronous Connection-Oriented) for headset
 * microphone and speaker routing.
 */
@Singleton
class BluetoothManager @Inject constructor(
    @ApplicationContext private val context: Context
) {

    private val _isHeadsetConnected = MutableStateFlow(false)
    val isHeadsetConnected: StateFlow<Boolean> = _isHeadsetConnected.asStateFlow()

    private val audioManager =
        context.getSystemService(Context.AUDIO_SERVICE) as AudioManager

    /**
     * Checks and updates the current headset connection status.
     */
    fun checkHeadset() {
        _isHeadsetConnected.value =
            audioManager.isBluetoothScoOn || audioManager.isWiredHeadsetOn
    }

    /**
     * Starts Bluetooth SCO audio connection for headset communication.
     */
    @Suppress("DEPRECATION")
    fun startBluetoothSco() {
        audioManager.startBluetoothSco()
        audioManager.isBluetoothScoOn = true
    }

    /**
     * Stops Bluetooth SCO audio connection.
     */
    @Suppress("DEPRECATION")
    fun stopBluetoothSco() {
        audioManager.stopBluetoothSco()
        audioManager.isBluetoothScoOn = false
    }

    /**
     * Returns whether Bluetooth is available and enabled on this device.
     */
    @Suppress("DEPRECATION")
    fun isBluetoothAvailable(): Boolean =
        BluetoothAdapter.getDefaultAdapter()?.isEnabled == true

    /**
     * Returns whether audio is currently routed through a Bluetooth device.
     */
    fun isBluetoothAudioActive(): Boolean = audioManager.isBluetoothScoOn
}
