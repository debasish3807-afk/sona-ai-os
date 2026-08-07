package com.sona.ai.tile

import android.content.Intent
import android.service.quicksettings.TileService
import dagger.hilt.android.AndroidEntryPoint

@AndroidEntryPoint
class SonaQuickSettingsTile : TileService() {

    override fun onStartListening() {
        super.onStartListening()
        qsTile?.apply {
            label = "Sona AI"
            contentDescription = "Open Sona AI"
            updateTile()
        }
    }

    override fun onClick() {
        super.onClick()
        val intent = packageManager.getLaunchIntentForPackage(packageName)?.apply {
            addFlags(Intent.FLAG_ACTIVITY_NEW_TASK)
        }
        intent?.let { startActivityAndCollapse(it) }
    }
}
