package com.sona.ai.features.beta.diagnostics

import android.content.Context
import android.os.Build
import androidx.core.content.pm.PackageInfoCompat
import dagger.hilt.android.qualifiers.ApplicationContext
import javax.inject.Inject
import javax.inject.Singleton

data class DeviceInfo(
    val model: String,
    val manufacturer: String,
    val os: String,
    val sdk: Int,
    val locale: String,
    val screenDensity: Float,
    val totalMemory: Long,
    val availableMemory: Long
)

@Singleton
class DeviceInfoCollector @Inject constructor(
    @ApplicationContext private val context: Context
) {

    fun collect(): DeviceInfo = DeviceInfo(
        model = Build.MODEL,
        manufacturer = Build.MANUFACTURER,
        os = "Android ${Build.VERSION.RELEASE}",
        sdk = Build.VERSION.SDK_INT,
        locale = context.resources.configuration.locales[0].toString(),
        screenDensity = context.resources.displayMetrics.density,
        totalMemory = Runtime.getRuntime().maxMemory(),
        availableMemory = Runtime.getRuntime().freeMemory()
    )

    fun getDeviceMap(): Map<String, String> = mapOf(
        "Model" to Build.MODEL,
        "Manufacturer" to Build.MANUFACTURER,
        "OS" to "Android ${Build.VERSION.RELEASE}",
        "SDK" to "${Build.VERSION.SDK_INT}",
        "Locale" to context.resources.configuration.locales[0].toString()
    )

    fun getAppMap(): Map<String, String> {
        val pm = context.packageManager.getPackageInfo(context.packageName, 0)
        return mapOf(
            "Version" to (pm.versionName ?: "?"),
            "Build" to "${PackageInfoCompat.getLongVersionCode(pm)}",
            "Package" to context.packageName
        )
    }

    fun getPerformanceMap(): Map<String, String> {
        val rt = Runtime.getRuntime()
        return mapOf(
            "Total Memory" to "${rt.maxMemory() / 1024 / 1024} MB",
            "Used" to "${(rt.totalMemory() - rt.freeMemory()) / 1024 / 1024} MB",
            "Free" to "${rt.freeMemory() / 1024 / 1024} MB",
            "Processors" to "${rt.availableProcessors()}"
        )
    }

    fun getNetworkMap(): Map<String, String> = mapOf(
        "Type" to "WiFi",
        "Status" to "Connected"
    )

    fun getStorageMap(): Map<String, String> = mapOf(
        "Internal" to "Available",
        "Cache" to "${context.cacheDir.totalSpace / 1024 / 1024} MB"
    )
}
