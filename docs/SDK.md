# JavaScript SDK Documentation

## Installation

### Option 1: Script Tag (Recommended for Merchants)

Add this single line to your store's HTML:

```html
<script src="https://cdn.neurocommerce.io/neurocommerce.js"></script>
<script>
  window.neurocommerce = new NeuroCommerceSDK({
    apiKey: 'sk_live_your_api_key_here'
  });
</script>
```

### Option 2: NPM Package

```bash
npm install @neurocommerce/tracking-sdk
```

```javascript
import NeuroCommerceSDK from '@neurocommerce/tracking-sdk';

const neurocommerce = new NeuroCommerceSDK({
  apiKey: 'sk_live_your_api_key_here'
});

window.neurocommerce = neurocommerce;
```

## Configuration

```javascript
new NeuroCommerceSDK({
  // Required
  apiKey: 'sk_live_xxx',
  
  // Optional
  apiHost: 'https://api.neurocommerce.io', // Custom API host
  customerId: 'customer_123',                // Set if user is logged in
  batchSize: 10,                             // Events per batch
  flushInterval: 5000,                       // Flush interval (ms)
  enableAutoTrack: true,                     // Auto-track page views, clicks
  enableExitIntent: true,                    // Detect exit intent
  debugMode: false                           // Console logging
});
```

## Auto-Tracking

The SDK automatically tracks:

- **Page Views**: When page loads
- **Scroll Depth**: Periodic scroll position updates
- **Product Clicks**: Clicks on elements with `data-product-id`
- **Form Submissions**: Checkout form submissions
- **Mouse Movement**: Periodic mouse position updates
- **Exit Intent**: When user moves mouse toward browser exit

## Manual Event Tracking

### Page View

```javascript
window.neurocommerce.trackPageView();

// Or with custom data
window.neurocommerce.track('page_view', {
  path: '/products',
  title: 'Our Products',
  category: 'electronics'
});
```

### Product View

```javascript
window.neurocommerce.trackProductView({
  id: 'prod_123',
  name: 'Wireless Headphones',
  price: 99.99,
  category: 'Electronics',
  image: 'https://...',
  sku: 'WH-1000'
});
```

### Add to Cart

```javascript
window.neurocommerce.trackAddToCart({
  id: 'prod_123',
  name: 'Wireless Headphones',
  price: 99.99,
  quantity: 1
});
```

### Checkout

```javascript
window.neurocommerce.trackCheckoutStart(totalCartValue);
```

### Order Completion

```javascript
window.neurocommerce.trackOrderComplete(
  'order_123',                    // Order ID
  129.98,                         // Total value
  [                               // Items
    { id: 'prod_123', qty: 1, price: 99.99 },
    { id: 'prod_124', qty: 1, price: 29.99 }
  ]
);
```

### Custom Events

```javascript
window.neurocommerce.track('custom_event_type', {
  key1: 'value1',
  key2: 'value2'
});
```

## HTML Data Attributes

Mark elements for automatic tracking:

```html
<!-- Product Click Tracking -->
<div data-product-id="prod_123" data-product-name="Widget">
  <img src="...">
  <h2>Widget</h2>
  <button>View Product</button>
</div>

<!-- Cart Value Tracking -->
<div data-cart-total="99.99">$99.99</div>

<!-- Cart Item Count Tracking -->
<span data-cart-count="3">3 items</span>
```

## Setting Customer ID

When user logs in:

```javascript
window.neurocommerce.customerId = 'customer_123';
```

## Session Management

Get session ID:

```javascript
const sessionId = window.neurocommerce.sessionId;
```

Destroy SDK (cleanup):

```javascript
window.neurocommerce.destroy();
```

## Events Format

All events sent to server follow this format:

```json
{
  "session_id": "sess_abc123",
  "customer_id": "cust_123",
  "events": [
    {
      "event_type": "page_view",
      "event_data": {
        "path": "/products"
      },
      "timestamp": "2024-01-14T12:00:00Z",
      "url": "https://store.com/products",
      "referrer": "https://google.com"
    }
  ]
}
```

## Batching & Performance

The SDK automatically:
- Batches events (configurable batch size)
- Flushes periodically (configurable interval)
- Retries failed requests
- Queues events offline

Example configuration for high-traffic store:

```javascript
new NeuroCommerceSDK({
  apiKey: 'sk_live_xxx',
  batchSize: 50,        // Larger batches
  flushInterval: 10000  // Less frequent flushes
});
```

## Troubleshooting

### Debug Mode

```javascript
new NeuroCommerceSDK({
  apiKey: 'sk_live_xxx',
  debugMode: true  // Logs all activity to console
});
```

### Check Events Queued

```javascript
console.log(window.neurocommerce.eventQueue);
```

### Manual Flush

```javascript
// Force flush all queued events
window.neurocommerce._flush();
```

### Verify API Key

```bash
curl -X POST https://api.neurocommerce.io/api/v1/events/batch \
  -H "api-key: sk_live_xxx" \
  -H "Content-Type: application/json" \
  -d '{"session_id":"test","events":[]}'
```

## Privacy & Compliance

The SDK respects:
- `Do Not Track` browser setting
- Cookie consent (wait for `window.dataLayer.push` before tracking)
- GDPR/CCPA data regulations

To comply with privacy laws:

```javascript
// Only initialize after user consents
if (window.dataLayer && window.dataLayer.userConsented) {
  window.neurocommerce = new NeuroCommerceSDK({...});
}

// Or check cookie consent
if (Cookies.get('analytics-consent') === 'true') {
  window.neurocommerce = new NeuroCommerceSDK({...});
}
```

## Examples

### Shopify Store

```html
<!-- In Shopify theme (theme.liquid) -->
<script src="https://cdn.neurocommerce.io/neurocommerce.js"></script>
<script>
  window.neurocommerce = new NeuroCommerceSDK({
    apiKey: '{{ shop.metafields.custom.neurocommerce_key }}',
    customerId: '{{ customer.id }}'
  });
  
  // Track product view on product page
  {% if product %}
    window.neurocommerce.trackProductView({
      id: '{{ product.id }}',
      name: '{{ product.title }}',
      price: {{ product.price | divided_by: 100.0 }},
      category: '{{ product.type }}'
    });
  {% endif %}
</script>
```

### WooCommerce Store

```php
// In functions.php
add_action('wp_footer', function() {
  $api_key = get_option('neurocommerce_api_key');
  if (!$api_key) return;
  ?>
  <script src="https://cdn.neurocommerce.io/neurocommerce.js"></script>
  <script>
    window.neurocommerce = new NeuroCommerceSDK({
      apiKey: '<?= $api_key ?>',
      customerId: '<?= get_current_user_id() ?>'
    });
    
    // Track WooCommerce events
    document.addEventListener('woocommerce_cart_updated', () => {
      const cart = wc_cart_fragments_params.cart_hash;
      window.neurocommerce.trackAddToCart({...});
    });
  </script>
  <?php
});
```

---

For issues or feature requests, visit [GitHub Issues](https://github.com/neurocommerce/neurocommerce-os/issues)
