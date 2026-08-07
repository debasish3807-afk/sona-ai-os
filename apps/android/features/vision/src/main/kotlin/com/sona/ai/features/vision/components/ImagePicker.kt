package com.sona.ai.features.vision.components

import android.net.Uri
import androidx.activity.compose.rememberLauncherForActivityResult
import androidx.activity.result.contract.ActivityResultContracts
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.layout.width
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.Image
import androidx.compose.material3.Button
import androidx.compose.material3.Icon
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedButton
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Modifier
import androidx.compose.ui.unit.dp

/**
 * Shared image/document picker component using Activity Result API.
 *
 * @param onImageSelected Callback when a file is selected
 * @param label Button label text
 * @param mimeTypes Array of MIME types to filter (defaults to images)
 */
@Composable
fun ImagePicker(
    onImageSelected: (Uri) -> Unit,
    label: String = "Select Image",
    mimeTypes: Array<String> = arrayOf("image/*")
) {
    var selectedUri by remember { mutableStateOf<Uri?>(null) }

    val launcher = rememberLauncherForActivityResult(
        contract = ActivityResultContracts.OpenDocument()
    ) { uri ->
        uri?.let {
            selectedUri = it
            onImageSelected(it)
        }
    }

    Button(
        onClick = { launcher.launch(mimeTypes) },
        modifier = Modifier.fillMaxWidth()
    ) {
        Icon(
            imageVector = Icons.Default.Image,
            contentDescription = null,
            modifier = Modifier.size(20.dp)
        )
        Spacer(modifier = Modifier.width(8.dp))
        Text(label)
    }

    selectedUri?.let { uri ->
        Spacer(modifier = Modifier.height(8.dp))
        Text(
            text = "Selected: ${uri.lastPathSegment ?: "file"}",
            style = MaterialTheme.typography.bodySmall,
            color = MaterialTheme.colorScheme.onSurfaceVariant
        )
    }
}

/**
 * Camera capture button for taking photos directly.
 */
@Composable
fun CameraCaptureButton(
    onImageCaptured: (Uri) -> Unit,
    label: String = "Take Photo"
) {
    OutlinedButton(
        onClick = { /* Camera capture integration via CameraX */ },
        modifier = Modifier.fillMaxWidth()
    ) {
        Text(label)
    }
}
