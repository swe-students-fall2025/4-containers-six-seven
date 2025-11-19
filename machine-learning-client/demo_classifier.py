"""
Demo script to test expense classifier with real examples.

This script demonstrates the expense classifier working with sample receipt data.
Note: First run will download the BART model (~1.6GB), which may take a few minutes.
"""

from expense_classifier import classify_expense, add_category_to_receipt, EXPENSE_CATEGORIES

# Test receipts covering different categories
test_receipts = [
    {
        "name": "Coffee Shop",
        "data": {
            "merchant": "Starbucks",
            "items": [
                {"name": "Latte", "price": 5.50},
                {"name": "Muffin", "price": 3.50}
            ],
            "total": 9.00
        }
    },
    {
        "name": "Grocery Store",
        "data": {
            "merchant": "Whole Foods",
            "items": [
                {"name": "Organic Milk", "price": 6.99},
                {"name": "Bread", "price": 4.50},
                {"name": "Eggs", "price": 5.00}
            ],
            "total": 16.49
        }
    },
    {
        "name": "Ride Share",
        "data": {
            "merchant": "Uber",
            "items": [],
            "total": 25.00
        }
    },
    {
        "name": "Retail Store",
        "data": {
            "merchant": "Target",
            "items": [
                {"name": "Shampoo", "price": 8.99},
                {"name": "Toothpaste", "price": 4.50}
            ],
            "total": 13.49
        }
    },
    {
        "name": "Pharmacy",
        "data": {
            "merchant": "CVS",
            "items": [
                {"name": "Prescription", "price": 25.00},
                {"name": "Vitamins", "price": 15.99}
            ],
            "total": 40.99
        }
    },
    {
        "name": "Movie Theater",
        "data": {
            "merchant": "AMC Theaters",
            "items": [
                {"name": "Movie Ticket", "price": 15.00},
                {"name": "Popcorn", "price": 8.00}
            ],
            "total": 23.00
        }
    },
    {
        "name": "Gas Station",
        "data": {
            "merchant": "Shell",
            "items": [
                {"name": "Gasoline", "price": 45.00}
            ],
            "total": 45.00
        }
    },
    {
        "name": "Sporting Goods",
        "data": {
            "merchant": "Nike Store",
            "items": [
                {"name": "Running Shoes", "price": 120.00},
                {"name": "Athletic Socks", "price": 15.00}
            ],
            "total": 135.00
        }
    },
    {
        "name": "Office Supply",
        "data": {
            "merchant": "Staples",
            "items": [
                {"name": "Printer Paper", "price": 25.00},
                {"name": "Pens", "price": 8.50}
            ],
            "total": 33.50
        }
    },
    {
        "name": "Unknown Store",
        "data": {
            "merchant": "Unknown",
            "items": [],
            "total": 10.00
        }
    }
]


def main():
    """Run classification demo on test receipts."""
    print("=" * 70)
    print("EXPENSE CLASSIFIER DEMO")
    print("=" * 70)
    print()
    print(f"Available categories: {', '.join(EXPENSE_CATEGORIES)}")
    print()
    print("Note: First run will download BART model (~1.6GB)")
    print("This may take a few minutes depending on your internet connection...")
    print()
    print("=" * 70)
    print()
    
    results = []
    
    for i, receipt in enumerate(test_receipts, 1):
        print(f"[{i}/{len(test_receipts)}] Testing: {receipt['name']}")
        print(f"  Merchant: {receipt['data']['merchant']}")
        
        if receipt['data']['items']:
            item_names = [item['name'] for item in receipt['data']['items']]
            print(f"  Items: {', '.join(item_names)}")
        else:
            print(f"  Items: (none)")
        
        print(f"  Total: ${receipt['data']['total']:.2f}")
        
        # Classify
        category = classify_expense(receipt['data'])
        
        print(f"  → Category: {category}")
        print()
        
        results.append({
            "name": receipt['name'],
            "merchant": receipt['data']['merchant'],
            "category": category
        })
    
    # Summary
    print("=" * 70)
    print("SUMMARY")
    print("=" * 70)
    print()
    
    for result in results:
        print(f"  {result['name']:20s} ({result['merchant']:20s}) → {result['category']}")
    
    print()
    print("=" * 70)
    print("Demo complete!")
    print("=" * 70)


if __name__ == "__main__":
    main()


