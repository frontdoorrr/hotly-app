import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:hotly_app/features/home/presentation/widgets/place_card.dart';
import 'package:hotly_app/shared/models/place.dart';

void main() {
  group('PlaceCard Widget Tests', () {
    final testPlace = Place(
      id: 'test_1',
      name: '테스트 카페',
      category: '카페',
      address: '서울시 강남구 테헤란로 123',
      latitude: 37.5665,
      longitude: 126.9780,
      rating: 4.5,
      tags: ['카페', '데이트'],
      imageUrl: 'https://example.com/image.jpg',
    );

    testWidgets('displays place information correctly', (tester) async {
      await tester.pumpWidget(
        MaterialApp(
          home: Scaffold(
            body: PlaceCard(
              place: testPlace,
              onTap: () {},
            ),
          ),
        ),
      );

      // Check if place name is displayed
      expect(find.text('테스트 카페'), findsOneWidget);

      // Check if address is displayed
      expect(find.text('서울시 강남구 테헤란로 123'), findsOneWidget);

      // Check if rating is displayed
      expect(find.text('4.5'), findsOneWidget);

      // Check if tags are displayed
      expect(find.text('#카페'), findsOneWidget);
      expect(find.text('#데이트'), findsOneWidget);
    });

    testWidgets('calls onTap when tapped', (tester) async {
      bool wasTapped = false;

      await tester.pumpWidget(
        MaterialApp(
          home: Scaffold(
            body: PlaceCard(
              place: testPlace,
              onTap: () {
                wasTapped = true;
              },
            ),
          ),
        ),
      );

      // Tap the card
      await tester.tap(find.byType(PlaceCard));
      await tester.pump();

      // Verify callback was called
      expect(wasTapped, isTrue);
    });

    testWidgets('shows star icon when rating > 0', (tester) async {
      await tester.pumpWidget(
        MaterialApp(
          home: Scaffold(
            body: PlaceCard(
              place: testPlace,
              onTap: () {},
            ),
          ),
        ),
      );

      // Check if star icon exists
      expect(find.byIcon(Icons.star), findsWidgets);
    });

    testWidgets('renders vertical card layout', (tester) async {
      await tester.pumpWidget(
        MaterialApp(
          home: Scaffold(
            body: PlaceCard(
              place: testPlace,
              onTap: () {},
              isHorizontal: false,
            ),
          ),
        ),
      );

      // Check if place name is still displayed
      expect(find.text('테스트 카페'), findsOneWidget);

      // Check if AspectRatio is used (vertical layout characteristic)
      expect(find.byType(AspectRatio), findsOneWidget);
    });
  });
}
