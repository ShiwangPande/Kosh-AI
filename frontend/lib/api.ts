/**
 * Kosh-AI API Client Library
 */
import Cookies from 'js-cookie';

const IS_SERVER = typeof window === 'undefined';
const API_URL = IS_SERVER
    ? (process.env.INTERNAL_API_URL || 'http://backend:8000/api/v1')
    : (process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1');

interface RequestOptions extends RequestInit {
    params?: Record<string, string>;
}

class ApiClient {
    private baseUrl: string;

    constructor(baseUrl: string) {
        this.baseUrl = baseUrl;
    }

    private getToken(): string | undefined {
        if (typeof window === 'undefined') return undefined;
        return Cookies.get('access_token');
    }

    setToken(access: string, refresh: string) {
        Cookies.set('access_token', access, { expires: 1 });
        Cookies.set('refresh_token', refresh, { expires: 7 });
    }

    clearTokens() {
        Cookies.remove('access_token');
        Cookies.remove('refresh_token');
    }

    private async request<T>(endpoint: string, options: RequestOptions = {}): Promise<T> {
        const { params, ...fetchOptions } = options;

        let url = `${this.baseUrl}${endpoint}`;
        if (params) {
            const searchParams = new URLSearchParams(params);
            url += `?${searchParams.toString()}`;
        }

        const token = this.getToken();
        const headers: Record<string, string> = {
            ...(fetchOptions.headers as Record<string, string>),
        };

        if (token) {
            headers['Authorization'] = `Bearer ${token}`;
        }

        if (!(fetchOptions.body instanceof FormData)) {
            headers['Content-Type'] = 'application/json';
        }

        const response = await fetch(url, { ...fetchOptions, headers });
        console.log(`[API] ${fetchOptions.method || 'GET'} ${url} -> ${response.status}`);

        if (response.status === 401) {
            this.clearTokens();
            if (typeof window !== 'undefined') {
                window.location.href = '/login';
            }
            throw new Error('Unauthorized');
        }

        if (!response.ok) {
            const error = await response.json().catch(() => ({ detail: 'Request failed' }));
            throw new Error(error.detail || `HTTP ${response.status}`);
        }

        if (response.status === 204) {
            return {} as T;
        }

        return response.json();
    }

    // ── Auth ──────────────────────────────────────────────
    async register(data: {
        email: string; password: string; business_name: string;
        phone?: string; business_type?: string;
    }) {
        return this.request('/auth/register', {
            method: 'POST',
            body: JSON.stringify(data),
        });
    }

    async login(email: string, password: string) {
        const res = await this.request<{
            access_token: string; refresh_token: string;
        }>('/auth/login', {
            method: 'POST',
            body: JSON.stringify({ email, password }),
        });
        this.setToken(res.access_token, res.refresh_token);
        return res;
    }

    async getMe() {
        return this.request('/auth/me');
    }

    async forgotPassword(email: string) {
        return this.request('/auth/forgot-password', {
            method: 'POST',
            body: JSON.stringify({ email }),
        });
    }

    async resetPassword(data: { email: string; token: string; new_password: string }) {
        return this.request('/auth/reset-password', {
            method: 'POST',
            body: JSON.stringify(data),
        });
    }

    // ── Merchants ─────────────────────────────────────────
    async updateProfile(data: Record<string, string>) {
        return this.request('/merchants/me', {
            method: 'PATCH',
            body: JSON.stringify(data),
        });
    }

    // ── Suppliers ─────────────────────────────────────────
    async getSuppliers(params?: Record<string, string>) {
        return this.request('/suppliers', { params });
    }

    async createSupplier(data: Record<string, any>) {
        return this.request('/suppliers', {
            method: 'POST',
            body: JSON.stringify(data),
        });
    }

    async getSupplier(id: string) {
        return this.request(`/suppliers/${id}`);
    }

    // ── Invoices ──────────────────────────────────────────
    async uploadInvoice(file: File, supplierId?: string) {
        const formData = new FormData();
        formData.append('file', file);
        if (supplierId) {
            formData.append('supplier_id', supplierId);
        }
        return this.request('/invoices/upload', {
            method: 'POST',
            body: formData,
        });
    }

    async getInvoices(params?: Record<string, string>) {
        return this.request('/invoices', { params });
    }

    async getInvoice(id: string) {
        return this.request(`/invoices/${id}`);
    }

    async getInvoiceItems(id: string) {
        return this.request<any[]>(`/invoices/${id}/items`);
    }

    async deleteInvoice(id: string) {
        return this.request(`/invoices/${id}`, {
            method: 'DELETE',
        });
    }

    async cancelInvoice(id: string) {
        return this.request(`/invoices/${id}/cancel`, {
            method: 'POST',
        });
    }

    async verifyInvoice(id: string, corrections: any[]) {
        return this.request(`/invoices/${id}/verify`, {
            method: 'POST',
            body: JSON.stringify({ corrections }),
        });
    }

    // ── Recommendations ───────────────────────────────────
    async getRecommendations(params?: Record<string, string>) {
        return this.request('/recommendations', { params });
    }

    async updateRecommendation(id: string, status: 'accepted' | 'rejected') {
        return this.request(`/recommendations/${id}`, {
            method: 'PATCH',
            body: JSON.stringify({ status }),
        });
    }

    // ── Admin ─────────────────────────────────────────────
    async getWeights() {
        return this.request('/admin/weights');
    }

    async updateWeights(weights: Record<string, number>) {
        return this.request('/admin/weights', {
            method: 'PUT',
            body: JSON.stringify(weights),
        });
    }

    async getAnalytics() {
        return this.request('/admin/analytics');
    }

    async getLogs(params?: Record<string, string>) {
        return this.request('/admin/logs', { params });
    }

    async flagMerchant(merchantId: string, reason: string) {
        return this.request(`/admin/merchants/${merchantId}/flag`, {
            method: 'POST',
            body: JSON.stringify({ reason }),
        });
    }

    async approveSupplier(supplierId: string) {
        return this.request(`/admin/suppliers/${supplierId}/approve`, {
            method: 'POST',
        });
    }

    // ── Orders ────────────────────────────────────────────
    async createOrder(data: any) {
        return this.request('/orders', {
            method: 'POST',
            body: JSON.stringify(data),
        });
    }

    async getOrders(params?: Record<string, string>) {
        return this.request('/orders', { params });
    }

    async getOrder(id: string) {
        return this.request(`/orders/${id}`);
    }

    async getSupplierProducts(supplierId: string, params?: Record<string, string>) {
        return this.request(`/suppliers/${supplierId}/products`, { params });
    }

    // ── Onboarding ────────────────────────────────────────
    async getOnboardingState() {
        return this.request<any>('/onboarding/state');
    }

    async advanceOnboardingStep() {
        return this.request<any>('/onboarding/advance', {
            method: 'POST',
        });
    }

    async completeOnboardingStep(step: string) {
        return this.request<any>('/onboarding/complete', {
            method: 'POST',
            body: JSON.stringify({ step }),
        });
    }

    async skipOnboarding() {
        return this.request<any>('/onboarding/skip', {
            method: 'POST',
        });
    }

    async resetOnboarding() {
        return this.request<any>('/onboarding/reset', {
            method: 'POST',
        });
    }

    // ── Documentation System ──────────────────────────────────

    async getDocCategories() {
        return this.request<string[]>('/docs/categories');
    }

    async listArticles() {
        return this.request<any[]>('/docs/articles');
    }

    async getDocArticle(slug: string) {
        return this.request<any>(`/docs/articles/${slug}`);
    }

    async searchDocs(query: string) {
        return this.request<any[]>(`/docs/search?q=${encodeURIComponent(query)}`);
    }
}

export const api = new ApiClient(API_URL);
export default api;
