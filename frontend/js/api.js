// API Wrapper module for B2B2C Platform
const API_BASE = "";

function getAuthHeaders() {
    const token = localStorage.getItem("token");
    return token ? { "Authorization": `Bearer ${token}` } : {};
}

async function apiFetch(endpoint, options = {}) {
    const headers = {
        "Content-Type": "application/json",
        ...getAuthHeaders(),
        ...(options.headers || {})
    };

    const response = await fetch(`${API_BASE}${endpoint}`, {
        ...options,
        headers
    });

    if (response.status === 401) {
        // Token expired or invalid
        localStorage.removeItem("token");
        if (window.location.pathname !== "/" && window.location.pathname !== "/app/index.html") {
            window.location.href = "/app/index.html";
        }
    }

    const data = await response.json();
    if (!response.ok) {
        throw new Error(data.detail || "Xatolik yuz berdi");
    }
    return data;
}

const api = {
    register: (companyData) => apiFetch("/auth/register", { method: "POST", body: JSON.stringify(companyData) }),
    login: async (email, password) => {
        const formData = new URLSearchParams();
        formData.append("username", email);
        formData.append("password", password);

        const res = await fetch(`${API_BASE}/auth/login`, {
            method: "POST",
            headers: { "Content-Type": "application/x-www-form-urlencoded" },
            body: formData
        });
        const data = await res.json();
        if (!res.ok) throw new Error(data.detail || "Login xatosi");
        localStorage.setItem("token", data.access_token);
        return data;
    },
    getMe: () => apiFetch("/companies/me"),
    getPartners: () => apiFetch("/companies/partners"),

    // Offers
    createOffer: (offerData) => apiFetch("/offers", { method: "POST", body: JSON.stringify(offerData) }),
    getSentOffers: () => apiFetch("/offers/sent"),
    getReceivedOffers: () => apiFetch("/offers/received"),
    respondOffer: (offerId, status, commissionPayer = "provider") =>
        apiFetch(`/offers/${offerId}/respond`, {
            method: "POST",
            body: JSON.stringify({ status, commission_payer: commissionPayer })
        }),
    getMyPartnerships: () => apiFetch("/offers/partnerships"),

    // Employee Codes
    generateCodes: (partnershipId, employees) =>
        apiFetch("/codes/generate", {
            method: "POST",
            body: JSON.stringify({ partnership_id: partnershipId, employees })
        }),
    getPartnershipCodes: (partnershipId) => apiFetch(`/codes/${partnershipId}`),

    // Redeem
    verifyCode: (code) => apiFetch("/redeem/verify", { method: "POST", body: JSON.stringify({ code }) }),
    confirmRedeem: (code, amount, note) =>
        apiFetch("/redeem/confirm", {
            method: "POST",
            body: JSON.stringify({ code, amount: parseFloat(amount), redeemed_by_note: note })
        }),

    // Admin Stats
    getAdminStats: () => apiFetch("/admin/stats")
};
