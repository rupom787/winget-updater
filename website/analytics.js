/**
 * Vercel Web Analytics Initialization
 * Safely guards initialization to prevent 404 console errors on GitHub Pages or local environments
 */
import { inject } from '@vercel/analytics';

try {
  if (typeof window !== 'undefined' && window.location) {
    const host = window.location.hostname;
    if (host.includes('vercel.app') || host.includes('vercel.live')) {
      inject({ mode: 'production' });
    }
  }
} catch (e) {
  // Gracefully ignore if analytics cannot load
}
