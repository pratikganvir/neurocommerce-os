/**
 * NeuroCommerce Tracking SDK
 * Client-side event tracking and intelligent persuasion
 */

class NeuroCommerceSDK {
  constructor(config) {
    this.config = {
      apiKey: config.apiKey,
      apiHost: config.apiHost || 'https://api.neurocommerce.io',
      batchSize: config.batchSize || 10,
      flushInterval: config.flushInterval || 5000,
      enableAutoTrack: config.enableAutoTrack !== false,
      enableExitIntent: config.enableExitIntent !== false,
      debugMode: config.debugMode || false,
      ...config
    };

    this.sessionId = this._generateSessionId();
    this.customerId = config.customerId;
    this.eventQueue = [];
    this.isInitialized = false;
    this.startTime = Date.now();

    this._init();
  }

  _init() {
    // Set up periodic flush
    this.flushInterval = setInterval(() => this._flush(), this.config.flushInterval);

    if (this.config.enableAutoTrack) {
      this._setupAutoTracking();
    }

    if (this.config.enableExitIntent) {
      this._setupExitIntent();
    }

    this.isInitialized = true;
    this._log('NeuroCommerce SDK initialized');
  }

  /**
   * Track a custom event
   */
  track(eventType, eventData = {}) {
    if (!this.isInitialized) return;

    const event = {
      event_type: eventType,
      event_data: eventData,
      timestamp: new Date().toISOString(),
      url: window.location.href,
      referrer: document.referrer
    };

    this.eventQueue.push(event);

    if (this.eventQueue.length >= this.config.batchSize) {
      this._flush();
    }
  }

  /**
   * Track page view
   */
  trackPageView() {
    this.track('page_view', {
      path: window.location.pathname,
      title: document.title,
      referrer: document.referrer
    });
  }

  /**
   * Track product view
   */
  trackProductView(productData) {
    this.track('product_view', {
      product_id: productData.id,
      product_name: productData.name,
      product_price: productData.price,
      product_category: productData.category,
      ...productData
    });
  }

  /**
   * Track add to cart
   */
  trackAddToCart(product) {
    this.track('add_to_cart', {
      product_id: product.id,
      product_name: product.name,
      product_price: product.price,
      quantity: product.quantity || 1
    });
  }

  /**
   * Track checkout start
   */
  trackCheckoutStart(cartValue) {
    this.track('checkout_start', {
      cart_value: cartValue,
      items_count: this._getCartItemCount()
    });
  }

  /**
   * Track order completion
   */
  trackOrderComplete(orderId, orderValue, items) {
    this.track('order_completed', {
      order_id: orderId,
      order_value: orderValue,
      items_count: items.length,
      items: items
    });
  }

  /**
   * Track scroll depth
   */
  _trackScrollDepth() {
    const windowHeight = window.innerHeight;
    const documentHeight = document.documentElement.scrollHeight;
    const scrollTop = window.scrollY;

    const scrollDepth = (scrollTop + windowHeight) / documentHeight;

    this.track('scroll', {
      scroll_depth: Math.min(scrollDepth, 1)
    });
  }

  /**
   * Track mouse movement for engagement
   */
  _trackMouseMovement() {
    let lastTrack = 0;

    document.addEventListener('mousemove', (e) => {
      const now = Date.now();
      if (now - lastTrack > 5000) { // Throttle to every 5 seconds
        this.track('mouse_movement', {
          x: e.clientX,
          y: e.clientY
        });
        lastTrack = now;
      }
    });
  }

  /**
   * Detect exit intent (user leaving without purchase)
   */
  _setupExitIntent() {
    document.addEventListener('mouseleave', () => {
      // Only track if on product or checkout page
      if (window.location.pathname.includes('products') || window.location.pathname.includes('checkout')) {
        this.track('exit_intent', {
          path: window.location.pathname
        });
      }
    });
  }

  /**
   * Set up automatic event tracking
   */
  _setupAutoTracking() {
    // Track page view on load
    this.trackPageView();

    // Track scroll depth periodically
    window.addEventListener('scroll', () => this._trackScrollDepth());

    // Track mouse movement
    this._trackMouseMovement();

    // Track clicks on products
    document.addEventListener('click', (e) => {
      const productElement = e.target.closest('[data-product-id]');
      if (productElement) {
        const productId = productElement.getAttribute('data-product-id');
        const productName = productElement.getAttribute('data-product-name');
        this.track('product_click', {
          product_id: productId,
          product_name: productName
        });
      }
    });

    // Track form submissions
    document.addEventListener('submit', (e) => {
      const form = e.target;
      if (form.id === 'checkout-form' || form.classList.contains('checkout-form')) {
        this.trackCheckoutStart(this._getCartValue());
      }
    });
  }

  /**
   * Flush queued events to server
   */
  async _flush() {
    if (this.eventQueue.length === 0) return;

    const events = this.eventQueue.splice(0, this.config.batchSize);

    try {
      const response = await fetch(`${this.config.apiHost}/api/v1/events/batch`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'api-key': this.config.apiKey
        },
        body: JSON.stringify({
          session_id: this.sessionId,
          customer_id: this.customerId,
          events: events,
          metadata: {
            sdk_version: '1.0.0',
            timestamp: new Date().toISOString()
          }
        })
      });

      if (!response.ok) {
        this._log(`Flush failed: ${response.statusText}`, 'error');
        // Re-queue events on failure
        this.eventQueue.unshift(...events);
      } else {
        this._log(`Flushed ${events.length} events`);
      }
    } catch (error) {
      this._log(`Flush error: ${error.message}`, 'error');
      // Re-queue events on error
      this.eventQueue.unshift(...events);
    }
  }

  /**
   * Get helper functions
   */
  _generateSessionId() {
    return `sess_${Math.random().toString(36).substr(2, 9)}`;
  }

  _getCartValue() {
    const cartElement = document.querySelector('[data-cart-total]');
    if (cartElement) {
      return parseFloat(cartElement.getAttribute('data-cart-total'));
    }
    return 0;
  }

  _getCartItemCount() {
    const countElement = document.querySelector('[data-cart-count]');
    if (countElement) {
      return parseInt(countElement.getAttribute('data-cart-count'));
    }
    return 0;
  }

  _log(message, level = 'info') {
    if (this.config.debugMode) {
      console[level](`[NeuroCommerce] ${message}`);
    }
  }

  /**
   * Clean up
   */
  destroy() {
    if (this.flushInterval) {
      clearInterval(this.flushInterval);
    }
    this._flush();
    this.isInitialized = false;
  }
}

// Export for use
if (typeof module !== 'undefined' && module.exports) {
  module.exports = NeuroCommerceSDK;
}
