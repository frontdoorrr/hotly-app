# ===== Consumer ProGuard Rules =====
# These rules are applied to consumers of this library

# Keep all public APIs
-keep public class com.hotly.hotly_app.** { public *; }

# Keep Flutter plugin registry
-keep class io.flutter.plugins.GeneratedPluginRegistrant { *; }

# Keep method channels
-keep class ** extends io.flutter.plugin.common.MethodChannel { *; }
-keep class ** extends io.flutter.plugin.common.EventChannel { *; }
