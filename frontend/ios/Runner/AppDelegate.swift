import Flutter
import UIKit

@main
@objc class AppDelegate: FlutterAppDelegate {

    private let appGroupId = "group.com.hotly.app.sharequeue"
    private let sharedKey = "SharedURLs"

    override func application(
        _ application: UIApplication,
        didFinishLaunchingWithOptions launchOptions: [UIApplication.LaunchOptionsKey: Any]?
    ) -> Bool {

        // Setup Method Channel for App Groups
        let controller = window?.rootViewController as! FlutterViewController
        let channel = FlutterMethodChannel(
            name: "com.hotly.app/share_queue",
            binaryMessenger: controller.binaryMessenger
        )

        channel.setMethodCallHandler { [weak self] (call, result) in
            guard let self = self else { return }

            switch call.method {
            case "getSharedUrls":
                let urls = self.getSharedUrlsFromAppGroup()
                result(urls)

            case "clearSharedUrls":
                self.clearSharedUrlsInAppGroup()
                result(true)

            default:
                result(FlutterMethodNotImplemented)
            }
        }

        GeneratedPluginRegistrant.register(with: self)
        return super.application(application, didFinishLaunchingWithOptions: launchOptions)
    }

    /// App Groups에서 공유된 URL 목록 가져오기
    private func getSharedUrlsFromAppGroup() -> [[String: Any]] {
        guard let userDefaults = UserDefaults(suiteName: appGroupId) else {
            print("AppDelegate: Failed to access App Groups")
            return []
        }

        let urls = userDefaults.array(forKey: sharedKey) as? [[String: Any]] ?? []
        print("AppDelegate: Found \(urls.count) shared URLs in App Groups")
        return urls
    }

    /// App Groups에서 공유된 URL 목록 삭제
    private func clearSharedUrlsInAppGroup() {
        guard let userDefaults = UserDefaults(suiteName: appGroupId) else {
            print("AppDelegate: Failed to access App Groups")
            return
        }

        userDefaults.removeObject(forKey: sharedKey)
        userDefaults.synchronize()
        print("AppDelegate: Cleared shared URLs from App Groups")
    }
}
