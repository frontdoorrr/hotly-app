import 'package:flutter/material.dart';
import '../../../core/theme/app_theme.dart';

enum ButtonVariant { primary, secondary, outline, ghost }

enum ButtonSize { sm, md, lg }

class AppButton extends StatefulWidget {
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
  State<AppButton> createState() => _AppButtonState();
}

class _AppButtonState extends State<AppButton> {
  bool _isPressed = false;

  bool get _canAnimate =>
      !widget.isDisabled && !widget.isLoading && widget.onPressed != null;

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final isEnabled =
        !widget.isDisabled && !widget.isLoading && widget.onPressed != null;

    final EdgeInsets padding;
    final double height;
    final double fontSize;

    switch (widget.size) {
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
        height = 44.0;
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
        if (widget.isLoading)
          SizedBox(
            width: 20,
            height: 20,
            child: CircularProgressIndicator(
              strokeWidth: 2,
              valueColor: AlwaysStoppedAnimation<Color>(
                widget.variant == ButtonVariant.primary
                    ? Colors.white
                    : theme.colorScheme.primary,
              ),
            ),
          )
        else if (widget.icon != null) ...[
          widget.icon!,
          const SizedBox(width: AppTheme.space2),
        ],
        Text(
          widget.text,
          style: TextStyle(fontSize: fontSize),
        ),
      ],
    );

    final ButtonStyle style;
    Widget button;

    switch (widget.variant) {
      case ButtonVariant.primary:
        style = ElevatedButton.styleFrom(
          padding: padding,
          minimumSize: Size(widget.width ?? 0, height),
        );
        button = SizedBox(
          width: widget.width,
          child: ElevatedButton(
            onPressed: isEnabled ? widget.onPressed : null,
            style: style,
            child: buttonChild,
          ),
        );
        break;

      case ButtonVariant.secondary:
        style = ElevatedButton.styleFrom(
          padding: padding,
          minimumSize: Size(widget.width ?? 0, height),
          backgroundColor: theme.colorScheme.secondary,
        );
        button = SizedBox(
          width: widget.width,
          child: ElevatedButton(
            onPressed: isEnabled ? widget.onPressed : null,
            style: style,
            child: buttonChild,
          ),
        );
        break;

      case ButtonVariant.outline:
        style = OutlinedButton.styleFrom(
          padding: padding,
          minimumSize: Size(widget.width ?? 0, height),
        );
        button = SizedBox(
          width: widget.width,
          child: OutlinedButton(
            onPressed: isEnabled ? widget.onPressed : null,
            style: style,
            child: buttonChild,
          ),
        );
        break;

      case ButtonVariant.ghost:
        style = TextButton.styleFrom(
          padding: padding,
          minimumSize: Size(widget.width ?? 0, height),
        );
        button = SizedBox(
          width: widget.width,
          child: TextButton(
            onPressed: isEnabled ? widget.onPressed : null,
            style: style,
            child: buttonChild,
          ),
        );
        break;
    }

    return GestureDetector(
      excludeFromSemantics: true,
      onTapDown: _canAnimate ? (_) => setState(() => _isPressed = true) : null,
      onTapUp: _canAnimate ? (_) => setState(() => _isPressed = false) : null,
      onTapCancel:
          _canAnimate ? () => setState(() => _isPressed = false) : null,
      child: AnimatedScale(
        scale: _isPressed ? 0.97 : 1.0,
        duration: const Duration(milliseconds: 200),
        curve: Curves.easeOut,
        child: button,
      ),
    );
  }
}
