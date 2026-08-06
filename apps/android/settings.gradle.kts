pluginManagement {
    repositories {
        google()
        mavenCentral()
        gradlePluginPortal()
    }
}

dependencyResolutionManagement {
    repositoriesMode.set(RepositoriesMode.FAIL_ON_PROJECT_REPOS)
    repositories {
        google()
        mavenCentral()
    }
}

rootProject.name = "sona-ai-android"

include(":app")
include(":core:domain")
include(":core:data")
include(":core:di")
include(":features:chat")
include(":features:settings")
include(":features:voice")
