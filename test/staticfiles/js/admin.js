class AdminDashboard extends CertBlockApp {
    constructor() {
        super();
        this.initializeCharts();
        this.setupEventListeners();
    }

    async initializeCharts() {
        const ctx = document.getElementById('transactionChart').getContext('2d');
        const data = await this.fetchTransactionData();
        
        new Chart(ctx, {
            type: 'line',
            data: {
                labels: data.labels,
                datasets: [{
                    label: 'Certificates Issued',
                    data: data.issuedCounts,
                    borderColor: 'rgb(79, 70, 229)',
                    tension: 0.1
                }]
            },
            options: {
                responsive: true,
                scales: {
                    y: {
                        beginAtZero: true
                    }
                }
            }
        });
    }

    async fetchTransactionData() {
        const response = await fetch('/api/admin/transaction-stats/');
        return await response.json();
    }

    async toggleUniversityStatus(universityId) {
        try {
            const response = await fetch(`/api/admin/universities/${universityId}/toggle-status/`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.getCsrfToken()
                }
            });
            
            if (response.ok) {
                window.location.reload();
            }
        } catch (error) {
            console.error('Error toggling university status:', error);
        }
    }

    async showUniversityDetails(universityId) {
        const response = await fetch(`/api/admin/universities/${universityId}/`);
        const university = await response.json();
        
        // Populate and show university details modal
        const modal = document.getElementById('universityDetailsModal');
        // ... populate modal with university data
        modal.classList.remove('hidden');
    }
}

// Initialize the admin dashboard
const adminDashboard = new AdminDashboard(); 