# Sona AI OS - ProGuard Rules

# Keep Retrofit interfaces
-keep,allowobfuscation interface com.sona.ai.data.remote.SonaApi

# Keep Gson models
-keepclassmembers class com.sona.ai.data.remote.dto.** { *; }

# Keep Hilt generated code
-keep class dagger.hilt.** { *; }

# Keep Room entities
-keep class com.sona.ai.data.local.entity.** { *; }

# Keep domain models (used in serialization)
-keep class com.sona.ai.domain.model.** { *; }
