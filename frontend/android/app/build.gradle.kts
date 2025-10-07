plugins {
    id("com.android.application")
    id("kotlin-android")
    // The Flutter Gradle Plugin must be applied after the Android and Kotlin Gradle plugins.
    id("dev.flutter.flutter-gradle-plugin")
    // Google Services for Firebase
    id("com.google.gms.google-services")
    // Firebase Crashlytics
    id("com.google.firebase.crashlytics")
}

android {
    namespace = "com.hotly.hotly_app"
    compileSdk = flutter.compileSdkVersion
    ndkVersion = flutter.ndkVersion

    compileOptions {
        sourceCompatibility = JavaVersion.VERSION_11
        targetCompatibility = JavaVersion.VERSION_11
    }

    kotlinOptions {
        jvmTarget = JavaVersion.VERSION_11.toString()
    }

    defaultConfig {
        applicationId = "com.hotly.hotly_app"
        // Firebase, Supabase, FCM require minSdk 21+
        minSdk = 21
        targetSdk = 34  // Android 14
        versionCode = flutter.versionCode
        versionName = flutter.versionName

        // MultiDex support for large apps
        multiDexEnabled = true

        // ProGuard consumer rules
        consumerProguardFiles("consumer-rules.pro")
    }

    // Signing configurations
    signingConfigs {
        create("release") {
            // TODO: Configure release signing in keystore.properties
            // For now, using debug keys
            storeFile = file("debug.keystore")
            storePassword = "android"
            keyAlias = "androiddebugkey"
            keyPassword = "android"
        }
    }

    buildTypes {
        getByName("debug") {
            applicationIdSuffix = ".debug"
            isDebuggable = true
            isMinifyEnabled = false
            isShrinkResources = false
        }

        getByName("release") {
            isDebuggable = false
            isMinifyEnabled = true  // Enable ProGuard/R8
            isShrinkResources = true  // Remove unused resources

            // ProGuard rules
            proguardFiles(
                getDefaultProguardFile("proguard-android-optimize.txt"),
                "proguard-rules.pro"
            )

            // Signing config
            signingConfig = signingConfigs.getByName("release")

            // Native crash reporting
            ndk {
                debugSymbolLevel = "FULL"
            }
        }

        // Staging build type
        create("staging") {
            initWith(getByName("debug"))
            applicationIdSuffix = ".staging"
            isDebuggable = true
            isMinifyEnabled = true
            isShrinkResources = true
            proguardFiles(
                getDefaultProguardFile("proguard-android-optimize.txt"),
                "proguard-rules.pro"
            )
            matchingFallbacks += listOf("debug")
        }
    }

    // Build features
    buildFeatures {
        buildConfig = true
    }
}

flutter {
    source = "../.."
}

dependencies {
    // Firebase
    implementation(platform("com.google.firebase:firebase-bom:32.7.0"))
    implementation("com.google.firebase:firebase-analytics-ktx")
    implementation("com.google.firebase:firebase-crashlytics-ktx")
    implementation("com.google.firebase:firebase-messaging-ktx")
    implementation("com.google.firebase:firebase-performance-ktx")

    // MultiDex
    implementation("androidx.multidex:multidex:2.0.1")

    // Kotlin
    implementation("org.jetbrains.kotlin:kotlin-stdlib-jdk8:1.9.22")
}
