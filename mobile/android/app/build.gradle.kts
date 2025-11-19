plugins {
    id("com.android.application")
    id("org.jetbrains.kotlin.android")
    id("com.google.devtools.ksp")
}

android {
    namespace = "com.mycoder.rocketchat"
    compileSdk = 34

    defaultConfig {
        applicationId = "com.mycoder.rocketchat"
        minSdk = 19  // Android 4.4 KitKat
        targetSdk = 34
        versionCode = 1
        versionName = "1.0.0"

        testInstrumentationRunner = "androidx.test.runner.AndroidJUnitRunner"

        vectorDrawables {
            useSupportLibrary = true
        }

        // MultiDex support for legacy devices
        multiDexEnabled = true

        buildConfigField("String", "MYCODER_API_URL", "\"http://localhost:8000\"")
        buildConfigField("String", "ROCKETCHAT_SERVER", "\"wss://chat.mycoder.local\"")
    }

    buildTypes {
        release {
            isMinifyEnabled = true
            isShrinkResources = true
            proguardFiles(
                getDefaultProguardFile("proguard-android-optimize.txt"),
                "proguard-rules.pro"
            )
            signingConfig = signingConfigs.getByName("debug")
        }
        debug {
            isMinifyEnabled = false
            applicationIdSuffix = ".debug"
            versionNameSuffix = "-DEBUG"
        }
    }

    flavorDimensions += "apiLevel"

    productFlavors {
        create("modern") {
            dimension = "apiLevel"
            minSdk = 29  // Android 10
            versionNameSuffix = "-modern"

            buildConfigField("String", "BUILD_VARIANT", "\"modern\"")
            buildConfigField("boolean", "SUPPORTS_MATERIAL3", "true")
            buildConfigField("boolean", "SUPPORTS_BIOMETRIC", "true")
        }

        create("legacy") {
            dimension = "apiLevel"
            minSdk = 19  // Android 4.4
            versionNameSuffix = "-legacy"

            buildConfigField("String", "BUILD_VARIANT", "\"legacy\"")
            buildConfigField("boolean", "SUPPORTS_MATERIAL3", "false")
            buildConfigField("boolean", "SUPPORTS_BIOMETRIC", "false")
        }
    }

    compileOptions {
        sourceCompatibility = JavaVersion.VERSION_17
        targetCompatibility = JavaVersion.VERSION_17

        // Enable desugaring for legacy compatibility
        isCoreLibraryDesugaringEnabled = true
    }

    kotlinOptions {
        jvmTarget = "17"
        freeCompilerArgs += listOf(
            "-opt-in=kotlin.RequiresOptIn",
            "-opt-in=kotlinx.coroutines.ExperimentalCoroutinesApi"
        )
    }

    buildFeatures {
        viewBinding = true
        buildConfig = true
        compose = true
    }

    composeOptions {
        kotlinCompilerExtensionVersion = "1.5.4"
    }

    packaging {
        resources {
            excludes += "/META-INF/{AL2.0,LGPL2.1}"
        }
    }
}

dependencies {
    // Core Android dependencies
    implementation("androidx.core:core-ktx:1.12.0")
    implementation("androidx.appcompat:appcompat:1.6.1")
    implementation("com.google.android.material:material:1.11.0")
    implementation("androidx.constraintlayout:constraintlayout:2.1.4")

    // MultiDex for legacy devices
    implementation("androidx.multidex:multidex:2.0.1")

    // Jetpack Compose - Modern variant only
    val composeVersion = "1.5.4"
    "modernImplementation"(platform("androidx.compose:compose-bom:2023.10.01"))
    "modernImplementation"("androidx.compose.ui:ui")
    "modernImplementation"("androidx.compose.ui:ui-graphics")
    "modernImplementation"("androidx.compose.ui:ui-tooling-preview")
    "modernImplementation"("androidx.compose.material3:material3")
    "modernImplementation"("androidx.activity:activity-compose:1.8.2")
    "modernDebugImplementation"("androidx.compose.ui:ui-tooling")

    // Lifecycle components
    val lifecycleVersion = "2.7.0"
    implementation("androidx.lifecycle:lifecycle-viewmodel-ktx:$lifecycleVersion")
    implementation("androidx.lifecycle:lifecycle-livedata-ktx:$lifecycleVersion")
    implementation("androidx.lifecycle:lifecycle-runtime-ktx:$lifecycleVersion")
    "modernImplementation"("androidx.lifecycle:lifecycle-viewmodel-compose:$lifecycleVersion")

    // Navigation
    val navVersion = "2.7.6"
    implementation("androidx.navigation:navigation-fragment-ktx:$navVersion")
    implementation("androidx.navigation:navigation-ui-ktx:$navVersion")
    "modernImplementation"("androidx.navigation:navigation-compose:$navVersion")

    // Room database
    val roomVersion = "2.6.1"
    implementation("androidx.room:room-runtime:$roomVersion")
    implementation("androidx.room:room-ktx:$roomVersion")
    ksp("androidx.room:room-compiler:$roomVersion")

    // Networking - Retrofit & OkHttp
    val retrofitVersion = "2.9.0"
    implementation("com.squareup.retrofit2:retrofit:$retrofitVersion")
    implementation("com.squareup.retrofit2:converter-gson:$retrofitVersion")
    implementation("com.squareup.okhttp3:okhttp:4.12.0")
    implementation("com.squareup.okhttp3:logging-interceptor:4.12.0")

    // WebSocket for RocketChat
    implementation("com.squareup.okhttp3:okhttp:4.12.0")

    // Coroutines
    val coroutinesVersion = "1.7.3"
    implementation("org.jetbrains.kotlinx:kotlinx-coroutines-core:$coroutinesVersion")
    implementation("org.jetbrains.kotlinx:kotlinx-coroutines-android:$coroutinesVersion")

    // JSON parsing
    implementation("com.google.code.gson:gson:2.10.1")

    // Image loading - Coil
    implementation("io.coil-kt:coil:2.5.0")
    "modernImplementation"("io.coil-kt:coil-compose:2.5.0")

    // DataStore for preferences
    implementation("androidx.datastore:datastore-preferences:1.0.0")

    // Work Manager for background tasks
    implementation("androidx.work:work-runtime-ktx:2.9.0")

    // Biometric authentication (modern only)
    "modernImplementation"("androidx.biometric:biometric:1.1.0")

    // Desugaring for Java 8+ APIs on legacy devices
    coreLibraryDesugaring("com.android.tools:desugar_jdk_libs:2.0.4")

    // Testing
    testImplementation("junit:junit:4.13.2")
    testImplementation("org.jetbrains.kotlinx:kotlinx-coroutines-test:$coroutinesVersion")
    testImplementation("androidx.arch.core:core-testing:2.2.0")
    androidTestImplementation("androidx.test.ext:junit:1.1.5")
    androidTestImplementation("androidx.test.espresso:espresso-core:3.5.1")
    "modernAndroidTestImplementation"(platform("androidx.compose:compose-bom:2023.10.01"))
    "modernAndroidTestImplementation"("androidx.compose.ui:ui-test-junit4")
}
