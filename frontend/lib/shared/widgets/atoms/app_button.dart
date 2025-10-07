import 'package:flutter/material.dart';
import '../../../core/theme/app_theme.dart';

enum ButtonVariant { primary, secondary, outline, ghost }

enum ButtonSize { sm, md, lg }

class AppButton extends StatelessWidget {
  final String text;
  final VoidCallback? onPressed;
  final ButtonVariant variant;
  final ButtonSize size;
  final bool isLoading;
  final bool isDisabled;
  final Widget? icon;
  final double? width;

  const AppButton({
    super.key,
    required this.text,
    this.onPressed,
    this.variant = ButtonVariant.primary,
    this.size = ButtonSize.md,
    this.isLoading = false,
    this.isDisabled = false,
    this.icon,
    this.width,
  });

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final isEnabled = !isDisabled && !isLoading && onPressed != null;

    // Size configuration
    final EdgeInsets padding;
    final double height;
    final double fontSize;

    switch (size) {
      case ButtonSize.sm:
        padding = const EdgeInsets.symmetric(
          horizontal: AppTheme.space4,
          vertical: AppTheme.space2,
        );
        height = 36.0;
        fontSize = 14.0;
        break;
      case ButtonSize.md:
        padding = const EdgeInsets.symmetric(
          horizontal: AppTheme.space6,
          vertical: AppTheme.space3,
        );
        height = 44.0; // Minimum touch target
        fontSize = 16.0;
        break;
      case ButtonSize.lg:
        padding = const EdgeInsets.symmetric(
          horizontal: AppTheme.space8,
          vertical: AppTheme.space4,
        );
        height = 52.0;
        fontSize = 18.0;
        break;
    }

    Widget buttonChild = Row(
      mainAxisSize: MainAxisSize.min,
      mainAxisAlignment: MainAxisAlignment.center,
      children: [
        if (isLoading)
          SizedBox(
            width: 20,
            height: 20,
            child: CircularProgressIndicator(
              strokeWidth: 2,
              valueColor: AlwaysStoppedAnimation<Color>(
                variant == ButtonVariant.primary
                    ? Colors.white
                    : theme.colorScheme.primary,
              ),
            ),
          )
        else if (icon != null) ...[
          icon!,
          const SizedBox(width: AppTheme.space2),
        ],
        Text(
          text,
          style: TextStyle(fontSize: fontSize),
        ),
      ],
    );

    final ButtonStyle style;

    switch (variant) {
      case ButtonVariant.primary:
        style = ElevatedButton.styleFrom(
          padding: padding,
          minimumSize: Size(width ?? 0, height),
        );
        return SizedBox(
          width: width,
          child: ElevatedButton(
            onPressed: isEnabled ? onPressed : null,
            style: style,
            child: buttonChild,
          ),
        );

      case ButtonVariant.secondary:
        style = ElevatedButton.styleFrom(
          padding: padding,
          minimumSize: Size(width ?? 0, height),
          backgroundColor: theme.colorScheme.secondary,
        );
        return SizedBox(
          width: width,
          child: ElevatedButton(
            onPressed: isEnabled ? onPressed : null,
            style: style,
            child: buttonChild,
          ),
        );

      case ButtonVariant.outline:
        style = OutlinedButton.styleFrom(
          padding: padding,
          minimumSize: Size(width ?? 0, height),
        );
        return SizedBox(
          width: width,
          child: OutlinedButton(
            onPressed: isEnabled ? onPressed : null,
            style: style,
            child: buttonChild,
          ),
        );

      case ButtonVariant.ghost:
        style = TextButton.styleFrom(
          padding: padding,
          minimumSize: Size(width ?? 0, height),
        );
        return SizedBox(
          width: width,
          child: TextButton(
            onPressed: isEnabled ? onPressed : null,
            style: style,
            child: buttonChild,
          ),
        );
    }
  }
}
