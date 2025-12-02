//
//  ShareViewController.swift
//  ShareExtension
//
//  iOS Share Extension for Hotly App
//  Receives shared URLs and saves them to App Groups for the main app to process.
//

import UIKit
import UniformTypeIdentifiers

class ShareViewController: UIViewController {

    // App Groups identifier - must match main app
    private let appGroupId = "group.com.hotly.app.sharequeue"
    private let sharedKey = "SharedURLs"

    // Supported URL patterns
    private let supportedPatterns = [
        "instagram.com",
        "naver.com",
        "blog.naver.com",
        "youtube.com",
        "youtu.be"
    ]

    override func viewDidLoad() {
        super.viewDidLoad()
        handleSharedContent()
    }

    private func handleSharedContent() {
        guard let extensionItems = extensionContext?.inputItems as? [NSExtensionItem] else {
            completeWithError()
            return
        }

        for extensionItem in extensionItems {
            guard let attachments = extensionItem.attachments else { continue }

            for attachment in attachments {
                // Handle URL type
                if attachment.hasItemConformingToTypeIdentifier(UTType.url.identifier) {
                    attachment.loadItem(forTypeIdentifier: UTType.url.identifier, options: nil) { [weak self] (item, error) in
                        if let url = item as? URL {
                            self?.processURL(url.absoluteString)
                        } else {
                            self?.completeWithError()
                        }
                    }
                    return
                }

                // Handle plain text (may contain URL)
                if attachment.hasItemConformingToTypeIdentifier(UTType.plainText.identifier) {
                    attachment.loadItem(forTypeIdentifier: UTType.plainText.identifier, options: nil) { [weak self] (item, error) in
                        if let text = item as? String {
                            self?.processText(text)
                        } else {
                            self?.completeWithError()
                        }
                    }
                    return
                }
            }
        }

        // No supported content found
        completeWithError()
    }

    private func processText(_ text: String) {
        // Extract URL from text
        let urlPattern = "https?://[^\\s]+"
        guard let regex = try? NSRegularExpression(pattern: urlPattern, options: .caseInsensitive),
              let match = regex.firstMatch(in: text, options: [], range: NSRange(text.startIndex..., in: text)),
              let range = Range(match.range, in: text) else {
            completeWithError()
            return
        }

        let urlString = String(text[range])
        processURL(urlString)
    }

    private func processURL(_ urlString: String) {
        // Validate URL is supported
        guard isSupportedURL(urlString) else {
            showUnsupportedAlert()
            return
        }

        // Save to App Groups
        saveToAppGroups(urlString)

        // Show success feedback and complete
        showSuccessAndComplete()
    }

    private func isSupportedURL(_ urlString: String) -> Bool {
        let lowercased = urlString.lowercased()
        return supportedPatterns.contains { lowercased.contains($0) }
    }

    private func saveToAppGroups(_ urlString: String) {
        guard let userDefaults = UserDefaults(suiteName: appGroupId) else {
            print("ShareExtension: Failed to access App Groups")
            return
        }

        // Create share item with metadata
        let shareItem: [String: Any] = [
            "id": UUID().uuidString,
            "url": urlString,
            "sharedAt": ISO8601DateFormatter().string(from: Date()),
            "status": "pending"
        ]

        // Get existing queue or create new
        var queue = userDefaults.array(forKey: sharedKey) as? [[String: Any]] ?? []

        // Check for duplicates
        let isDuplicate = queue.contains { item in
            (item["url"] as? String) == urlString
        }

        if !isDuplicate {
            queue.append(shareItem)

            // Limit queue size to 20
            if queue.count > 20 {
                queue = Array(queue.suffix(20))
            }

            userDefaults.set(queue, forKey: sharedKey)
            userDefaults.synchronize()

            print("ShareExtension: Saved URL to queue: \(urlString)")
        } else {
            print("ShareExtension: URL already in queue: \(urlString)")
        }
    }

    private func showSuccessAndComplete() {
        DispatchQueue.main.async { [weak self] in
            let alert = UIAlertController(
                title: "Hotly에 추가됨",
                message: "링크가 분석 대기열에 추가되었습니다.",
                preferredStyle: .alert
            )

            self?.present(alert, animated: true) {
                DispatchQueue.main.asyncAfter(deadline: .now() + 1.0) {
                    self?.completeRequest()
                }
            }
        }
    }

    private func showUnsupportedAlert() {
        DispatchQueue.main.async { [weak self] in
            let alert = UIAlertController(
                title: "지원하지 않는 링크",
                message: "Instagram, 네이버 블로그, YouTube 링크만 지원됩니다.",
                preferredStyle: .alert
            )
            alert.addAction(UIAlertAction(title: "확인", style: .default) { _ in
                self?.completeRequest()
            })

            self?.present(alert, animated: true)
        }
    }

    private func completeRequest() {
        extensionContext?.completeRequest(returningItems: nil, completionHandler: nil)
    }

    private func completeWithError() {
        let error = NSError(domain: "com.hotly.shareextension", code: 1, userInfo: nil)
        extensionContext?.cancelRequest(withError: error)
    }
}

