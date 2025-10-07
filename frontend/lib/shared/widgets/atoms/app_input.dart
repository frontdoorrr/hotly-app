import 'package:flutter/material.dart';
import '../../../core/theme/app_theme.dart';

class AppInput extends StatelessWidget {
  final String? label;
  final String? placeholder;
  final String? hintText; // Alias for placeholder
  final String? value;
  final ValueChanged<String>? onChanged;
  final String? errorText;
  final FormFieldValidator<String>? validator;
  final bool isDisabled;
  final bool isRequired;
  final TextInputType? keyboardType;
  final bool obscureText;
  final Widget? leftIcon;
  final Widget? prefixIcon; // Alias for leftIcon
  final Widget? rightIcon;
  final Widget? suffixIcon; // Alias for rightIcon
  final int? maxLines;
  final int? maxLength;
  final TextEditingController? controller;

  const AppInput({
    super.key,
    this.label,
    this.placeholder,
    this.hintText,
    this.value,
    this.onChanged,
    this.errorText,
    this.validator,
    this.isDisabled = false,
    this.isRequired = false,
    this.keyboardType,
    this.obscureText = false,
    this.leftIcon,
    this.prefixIcon,
    this.rightIcon,
    this.suffixIcon,
    this.maxLines = 1,
    this.maxLength,
    this.controller,
  });

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        if (label != null) ...[
          Row(
            children: [
              Text(
                label!,
                style: theme.textTheme.labelMedium,
              ),
              if (isRequired)
                Text(
                  ' *',
                  style: theme.textTheme.labelMedium?.copyWith(
                    color: theme.colorScheme.error,
                  ),
                ),
            ],
          ),
          const SizedBox(height: AppTheme.space2),
        ],
        TextFormField(
          controller: controller,
          onChanged: onChanged,
          validator: validator,
          enabled: !isDisabled,
          keyboardType: keyboardType,
          obscureText: obscureText,
          maxLines: maxLines,
          maxLength: maxLength,
          decoration: InputDecoration(
            hintText: hintText ?? placeholder,
            errorText: errorText,
            prefixIcon: prefixIcon ?? leftIcon,
            suffixIcon: suffixIcon ?? rightIcon,
          ),
        ),
      ],
    );
  }
}
