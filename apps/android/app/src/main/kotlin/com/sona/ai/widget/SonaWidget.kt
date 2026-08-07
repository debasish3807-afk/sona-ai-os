package com.sona.ai.widget

import android.app.PendingIntent
import android.appwidget.AppWidgetManager
import android.appwidget.AppWidgetProvider
import android.content.Context
import android.content.Intent
import android.widget.RemoteViews

class SonaWidget : AppWidgetProvider() {

    override fun onUpdate(
        context: Context,
        appWidgetManager: AppWidgetManager,
        appWidgetIds: IntArray
    ) {
        appWidgetIds.forEach { id ->
            val views = RemoteViews(
                context.packageName,
                android.R.layout.simple_list_item_1
            )

            val intent = Intent(context, Class.forName("com.sona.ai.MainActivity"))
            val pending = PendingIntent.getActivity(
                context,
                0,
                intent,
                PendingIntent.FLAG_IMMUTABLE
            )

            views.setOnClickPendingIntent(android.R.id.text1, pending)
            views.setTextViewText(android.R.id.text1, "Sona AI - Tap to open")
            appWidgetManager.updateAppWidget(id, views)
        }
    }
}
