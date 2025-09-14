// KYC Risk Assessment JavaScript
document.addEventListener('DOMContentLoaded', function() {
    const riskForm = document.getElementById('risk-form');
    const portfolioResults = document.getElementById('portfolio-results');
    const warningsContainer = document.getElementById('kyc-warnings');
    const warningMessages = document.getElementById('warning-messages');
    
    // Track KYC responses for validation
    let currentResponses = {};
    
    // Add change listeners to all radio buttons
    const radioButtons = document.querySelectorAll('input[type="radio"][name="horizon_score"], input[type="radio"][name="loss_tolerance"], input[type="radio"][name="experience_score"], input[type="radio"][name="financial_score"], input[type="radio"][name="goal_score"], input[type="radio"][name="sleep_score"]');
    
    radioButtons.forEach(radio => {
        radio.addEventListener('change', function() {
            currentResponses[this.name] = parseInt(this.value);
            validateResponses();
        });
    });
    
    // Simple client-side consistency validation
    function validateResponses() {
        if (Object.keys(currentResponses).length < 6) return; // Not all questions answered
        
        const warnings = [];
        
        // Short horizon + high risk tolerance
        if (currentResponses.horizon_score < 30 && currentResponses.loss_tolerance > 70) {
            warnings.push({
                message: "Short-term investment with high risk tolerance - consider a more conservative approach",
                severity: "warning"
            });
        }
        
        // Low experience + aggressive goals
        if (currentResponses.experience_score < 30 && currentResponses.goal_score > 80) {
            warnings.push({
                message: "Limited experience with aggressive growth goals - consider starting with a moderate approach",
                severity: "warning"
            });
        }
        
        // Low financial capacity + high risk appetite
        if (currentResponses.financial_score < 40 && currentResponses.loss_tolerance > 60) {
            warnings.push({
                message: "Limited financial capacity with high risk appetite - important to start conservatively",
                severity: "error"
            });
        }
        
        // Sleep test vs loss tolerance mismatch
        if (Math.abs(currentResponses.sleep_score - currentResponses.loss_tolerance) > 40) {
            warnings.push({
                message: "Contradiction between stated and practical loss tolerance - we'll use the more conservative limit",
                severity: "warning"
            });
        }
        
        // Display warnings
        displayWarnings(warnings);
    }
    
    function displayWarnings(warnings) {
        if (warnings.length === 0) {
            warningsContainer.classList.add('hidden');
            return;
        }
        
        let warningHtml = '';
        warnings.forEach(warning => {
            const severityClass = warning.severity === 'error' ? 'warning-severity-error' : '';
            warningHtml += `<div class="warning-item ${severityClass}">${warning.message}</div>`;
        });
        
        warningMessages.innerHTML = warningHtml;
        warningsContainer.classList.remove('hidden');
    }
    
    // Handle form submission
    riskForm.addEventListener('submit', async function(e) {
        e.preventDefault();
        
        const formData = new FormData(this);
        const submitButton = this.querySelector('.submit-button');
        
        // Validate all questions are answered
        const requiredFields = ['horizon_score', 'loss_tolerance', 'experience_score', 'financial_score', 'goal_score', 'sleep_score'];
        let allAnswered = true;
        let missingFields = [];
        
        requiredFields.forEach(field => {
            const value = formData.get(field);
            if (!value) {
                allAnswered = false;
                missingFields.push(field);
            }
        });
        
        if (!allAnswered) {
            console.log('Missing fields:', missingFields);
            alert(`Please answer all questions before proceeding. Missing: ${missingFields.join(', ')}`);
            return;
        }
        
        console.log('All questions answered, submitting form...');
        
        // Show loading state
        submitButton.textContent = 'Analyzing Your Risk Profile...';
        submitButton.disabled = true;
        
        try {
            console.log('Sending request to /api/calculate-portfolio...');
            
            const response = await fetch('/api/calculate-portfolio', {
                method: 'POST',
                body: formData
            });
            
            console.log('Response status:', response.status);
            console.log('Response ok:', response.ok);
            
            if (!response.ok) {
                const errorText = await response.text();
                console.error('Server error response:', errorText);
                throw new Error(`Server error: ${response.status} - ${errorText}`);
            }
            
            const data = await response.json();
            console.log('Portfolio data received:', data);
            
            // Check for blocking inconsistencies
            if (data.error === 'inconsistent_responses') {
                displayBlockingError(data);
                return;
            }
            
            displayPortfolioResults(data);
            
        } catch (error) {
            console.error('Error details:', error);
            console.error('Error stack:', error.stack);
            
            // Try to get more error details
            if (error.message.includes('Network response was not ok')) {
                console.error('HTTP error - check server logs');
            }
            
            alert('Error calculating portfolio. Please check the console for details and try again.');
        } finally {
            // Reset button
            submitButton.textContent = 'Create My Quantica Portfolio';
            submitButton.disabled = false;
        }
    });
    
    function displayBlockingError(errorData) {
        let errorHtml = '<div class="error-container" style="background: rgba(239, 68, 68, 0.1); border: 1px solid rgba(239, 68, 68, 0.3); border-radius: var(--border-radius); padding: 1.5rem; margin: 1.5rem 0;">';
        errorHtml += '<h4 style="color: #ef4444; margin-bottom: 1rem;">⚠️ Cannot Calculate Portfolio</h4>';
        errorHtml += '<p style="margin-bottom: 1rem;">Your responses contain inconsistencies that prevent us from creating a suitable portfolio:</p>';
        
        errorData.kyc_profile.inconsistencies.forEach(inc => {
            errorHtml += `<div style="background: rgba(239, 68, 68, 0.05); padding: 0.75rem; border-radius: var(--border-radius); margin-bottom: 0.5rem; border-left: 3px solid #ef4444;">${inc.message}</div>`;
        });
        
        errorHtml += '<p style="margin-top: 1rem; color: var(--text-secondary);">Please review your answers and try again with more consistent responses.</p>';
        errorHtml += '</div>';
        
        // Insert error message before the submit button
        const submitButton = document.querySelector('.submit-button');
        submitButton.insertAdjacentHTML('beforebegin', errorHtml);
        
        // Remove error after 10 seconds
        setTimeout(() => {
            const errorContainer = document.querySelector('.error-container');
            if (errorContainer) errorContainer.remove();
        }, 10000);
    }
    
    function displayPortfolioResults(data) {
        // Update summary stats
        document.getElementById('expected-return').textContent = data.performance_metrics.expected_return_annual.toFixed(1) + '%';
        document.getElementById('volatility').textContent = data.performance_metrics.volatility_annual.toFixed(1) + '%';
        document.getElementById('sharpe-ratio').textContent = data.performance_metrics.sharpe_ratio.toFixed(2);
        
        // Create portfolio allocation chart
        createPortfolioChart(data.portfolio_allocation.percentages);

        // Create performance chart
        if (data.performance_history && data.performance_history.dates) {
            createPerformanceChart(data.performance_history);
        }

        // Create portfolio details table
        createPortfolioDetails(data.portfolio_allocation);

        // NEW: Display KYC profile information
        displayKYCProfile(data.risk_assessment);
        
        // Show results
        portfolioResults.classList.remove('hidden');
        portfolioResults.scrollIntoView({ behavior: 'smooth' });
    }
    
    function displayKYCProfile(riskAssessment) {
        // Create KYC profile section if it doesn't exist
        let kycProfileContainer = document.getElementById('kyc-profile-container');
        if (!kycProfileContainer) {
            kycProfileContainer = document.createElement('div');
            kycProfileContainer.id = 'kyc-profile-container';

            // Insert after portfolio summary
            const portfolioSummary = document.querySelector('.portfolio-summary');
            portfolioSummary.parentNode.insertBefore(kycProfileContainer, portfolioSummary.nextSibling);
        }

        let html = `
            <div class="kyc-profile-section">
                <h3>Your Risk Profile</h3>
                <div class="risk-profile-card">
                    <div class="profile-header">
                        <h4>${riskAssessment.category}</h4>
                        <div class="confidence-score">Risk Score: ${riskAssessment.composite_score.toFixed(0)}/100</div>
                    </div>
                    <div class="risk-constraints">
                        <div class="constraint-item">
                            <span class="label">Risk Level:</span>
                            <span class="value">${riskAssessment.risk_level}/10</span>
                        </div>
                        <div class="constraint-item">
                            <span class="label">Category (Hebrew):</span>
                            <span class="value">${riskAssessment.category_hebrew}</span>
                        </div>
                    </div>
        `;
        
        // Add warnings if any (skip for now since API structure is different)
        // if (riskAssessment.has_warnings) {
        //     html += '<div class="profile-warnings"><h5>Advisory Notes:</h5>';
        //     riskAssessment.inconsistencies.forEach(inc => {
        //         html += `<div class="warning-note">${inc.message}</div>`;
        //     });
        //     html += '</div>';
        // }
        
        html += '</div></div>';
        
        kycProfileContainer.innerHTML = html;
    }
    
    function createPortfolioChart(portfolio) {
        const ctx = document.getElementById('portfolioChart').getContext('2d');
        
        // Destroy existing chart if it exists
        if (window.portfolioChart && typeof window.portfolioChart.destroy === 'function') {
            window.portfolioChart.destroy();
        }
        
        const labels = Object.keys(portfolio);
        const data = Object.values(portfolio).map(val => val * 100);
        const colors = [
            '#3b82f6', '#10b981', '#f59e0b', '#ef4444', 
            '#8b5cf6', '#06b6d4', '#84cc16', '#f97316'
        ];
        
        window.portfolioChart = new Chart(ctx, {
            type: 'doughnut',
            data: {
                labels: labels,
                datasets: [{
                    data: data,
                    backgroundColor: colors.slice(0, labels.length),
                    borderWidth: 2,
                    borderColor: '#ffffff'
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        position: 'bottom',
                        labels: {
                            padding: 20,
                            font: { size: 14 }
                        }
                    },
                    tooltip: {
                        callbacks: {
                            label: function(context) {
                                return context.label + ': ' + context.parsed.toFixed(1) + '%';
                            }
                        }
                    }
                }
            }
        });
    }
    
    function createPerformanceChart(performanceHistory) {
        // Create performance chart container if it doesn't exist
        let perfChartContainer = document.getElementById('performance-chart-container');
        if (!perfChartContainer) {
            perfChartContainer = document.createElement('div');
            perfChartContainer.id = 'performance-chart-container';

            // Insert after portfolio chart
            const portfolioChartDiv = document.querySelector('.portfolio-chart');
            portfolioChartDiv.parentNode.insertBefore(perfChartContainer, portfolioChartDiv.nextSibling);
        }

        // Always update the content (for when user changes answers)
        perfChartContainer.innerHTML = `
            <h3>Portfolio Performance Over Time</h3>
            <div style="position: relative; height: 400px; margin: 2rem 0;">
                <canvas id="performanceChart"></canvas>
            </div>
            <div class="performance-stats">
                <div class="stat">
                    <h4>Total Return</h4>
                    <span id="total-return">${performanceHistory.total_return_pct.toFixed(1)}%</span>
                </div>
                <div class="stat">
                    <h4>Period</h4>
                    <span id="period">${performanceHistory.years.toFixed(1)} years</span>
                </div>
                <div class="stat">
                    <h4>Final Value</h4>
                    <span id="final-value">₪${performanceHistory.final_value.toLocaleString('he-IL', {maximumFractionDigits: 0})}</span>
                </div>
            </div>
        `;
        
        const ctx = document.getElementById('performanceChart').getContext('2d');
        
        // Destroy existing chart if it exists
        if (window.performanceChart && typeof window.performanceChart.destroy === 'function') {
            window.performanceChart.destroy();
        }
        
        // Create chart data from performance history
        const chartData = performanceHistory.dates.map((date, index) => ({
            x: date,
            y: performanceHistory.values[index]
        }));

        // Add baseline (initial investment)
        const baselineData = performanceHistory.dates.map(date => ({
            x: date,
            y: performanceHistory.initial_investment
        }));
        
        // Store initial investment for tooltip callback
        const initialInvestment = performanceHistory.initial_investment;

        window.performanceChart = new Chart(ctx, {
            type: 'line',
            data: {
                datasets: [{
                    label: 'Portfolio Value',
                    data: chartData,
                    borderColor: '#8b5cf6',
                    backgroundColor: 'rgba(139, 92, 246, 0.1)',
                    borderWidth: 3,
                    fill: true,
                    tension: 0.1
                }, {
                    label: 'Initial Investment',
                    data: baselineData,
                    borderColor: '#64748b',
                    backgroundColor: 'transparent',
                    borderWidth: 2,
                    borderDash: [5, 5],
                    fill: false,
                    pointRadius: 0
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                interaction: {
                    intersect: false,
                    mode: 'index'
                },
                plugins: {
                    legend: {
                        labels: {
                            color: '#ffffff',
                            font: { size: 14 }
                        }
                    },
                    tooltip: {
                        backgroundColor: 'rgba(26, 26, 30, 0.9)',
                        titleColor: '#ffffff',
                        bodyColor: '#ffffff',
                        borderColor: '#8b5cf6',
                        borderWidth: 1,
                        callbacks: {
                            label: function(context) {
                                const value = context.parsed.y;
                                const pnl = value - initialInvestment;
                                const pnlPercent = (pnl / initialInvestment * 100).toFixed(1);
                                return `${context.dataset.label}: ₪${value.toLocaleString('he-IL', {maximumFractionDigits: 0})} (${pnlPercent > 0 ? '+' : ''}${pnlPercent}%)`;
                            }
                        }
                    }
                },
                scales: {
                    x: {
                        type: 'time',
                        time: {
                            unit: 'month',
                            displayFormats: { month: 'MMM yyyy' }
                        },
                        grid: { color: 'rgba(255, 255, 255, 0.1)' },
                        ticks: { color: '#a1a1aa' }
                    },
                    y: {
                        beginAtZero: false,
                        grid: { color: 'rgba(255, 255, 255, 0.1)' },
                        ticks: {
                            color: '#a1a1aa',
                            callback: function(value) {
                                return '₪' + value.toLocaleString('he-IL', {maximumFractionDigits: 0});
                            }
                        }
                    }
                }
            }
        });
    }
    
    function createPortfolioDetails(portfolioAllocation) {
        const detailsContainer = document.getElementById('portfolio-details');

        // Helper function to format asset names
        function formatAssetName(assetName) {
            return assetName
                .replace(/_/g, ' ')
                .replace(/([A-Z])/g, ' $1')
                .replace(/\b\w/g, l => l.toUpperCase())
                .trim();
        }

        let html = '<h3>Portfolio Allocation Details</h3>';

        // Add table header
        html += `<div class="allocation-table">
            <div class="allocation-row header-row">
                <div class="asset-name">Asset</div>
                <div class="asset-percentage">Allocation</div>
                <div class="asset-amount">Amount (₪)</div>
            </div>`;

        // Add asset rows
        for (const [asset, percentage] of Object.entries(portfolioAllocation.percentages)) {
            const percentageDisplay = (percentage * 100).toFixed(1);
            const amount = portfolioAllocation.amounts_ils[asset];

            html += `
                <div class="allocation-row">
                    <div class="asset-name">${formatAssetName(asset)}</div>
                    <div class="asset-percentage">${percentageDisplay}%</div>
                    <div class="asset-amount">₪${Number(amount).toLocaleString('he-IL', {maximumFractionDigits: 0})}</div>
                </div>
            `;
        }

        html += '</div>';

        // Add total row
        html += `<div class="total-row">
            <div class="total-label">Total Investment:</div>
            <div class="total-amount">₪${Number(portfolioAllocation.total_invested).toLocaleString('he-IL', {maximumFractionDigits: 0})}</div>
        </div>`;

        detailsContainer.innerHTML = html;
    }
});

// Add CSS for KYC profile and improved styling
const style = document.createElement('style');
style.textContent = `
    .kyc-profile-section {
        background: var(--surface-elevated);
        padding: 2rem;
        border-radius: var(--border-radius-lg);
        box-shadow: var(--shadow-lg);
        border: 1px solid var(--border-color);
        margin: 2rem 0;
    }
    
    .kyc-profile-section h3 {
        color: var(--text-primary);
        margin-bottom: 1.5rem;
        font-size: 1.5rem;
    }
    
    .risk-profile-card {
        background: var(--surface-color);
        border-radius: var(--border-radius);
        padding: 1.5rem;
        border: 1px solid var(--border-color);
    }
    
    .profile-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 1.5rem;
        padding-bottom: 1rem;
        border-bottom: 1px solid var(--border-color);
    }
    
    .profile-header h4 {
        font-size: 1.25rem;
        color: var(--primary-color);
        margin: 0;
    }
    
    .confidence-score {
        background: var(--primary-color);
        color: white;
        padding: 0.5rem 1rem;
        border-radius: 2rem;
        font-size: 0.875rem;
        font-weight: 600;
    }
    
    .risk-constraints {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
        gap: 1rem;
    }
    
    .constraint-item {
        display: flex;
        justify-content: space-between;
        padding: 0.75rem;
        background: var(--background-secondary);
        border-radius: var(--border-radius);
        border: 1px solid var(--border-color);
    }
    
    .constraint-item .label {
        color: var(--text-secondary);
        font-weight: 500;
    }
    
    .constraint-item .value {
        color: var(--text-primary);
        font-weight: 600;
    }
    
    .profile-warnings {
        margin-top: 1.5rem;
        padding-top: 1rem;
        border-top: 1px solid var(--border-color);
    }
    
    .profile-warnings h5 {
        color: var(--accent-color);
        margin-bottom: 0.75rem;
        font-size: 1rem;
    }
    
    .warning-note {
        background: rgba(245, 158, 11, 0.05);
        padding: 0.75rem;
        border-radius: var(--border-radius);
        margin-bottom: 0.5rem;
        border-left: 3px solid var(--accent-color);
        color: var(--text-secondary);
    }
    
    .allocation-table {
        margin-top: 1rem;
        border-radius: 8px;
        overflow: hidden;
        border: 1px solid var(--border-color);
    }
    
    .allocation-row {
        display: grid;
        grid-template-columns: 2fr 1fr 1fr;
        padding: 1rem;
        border-bottom: 1px solid var(--border-color);
        background: var(--surface-color);
    }

    .header-row {
        background: var(--primary-color);
        color: white;
        font-weight: 600;
        position: sticky;
        top: 0;
    }

    .header-row .asset-name,
    .header-row .asset-percentage,
    .header-row .asset-amount {
        color: white;
    }
    
    .allocation-row:nth-child(even) {
        background: var(--surface-elevated);
    }
    
    .allocation-row:last-child {
        border-bottom: none;
    }
    
    .asset-name {
        font-weight: 600;
        color: var(--text-primary);
    }
    
    .asset-percentage {
        text-align: center;
        font-weight: 500;
        color: var(--primary-color);
    }
    
    .asset-amount {
        text-align: right;
        font-weight: 500;
        color: var(--text-primary);
    }

    .total-row {
        display: grid;
        grid-template-columns: 2fr 1fr;
        padding: 1rem;
        background: var(--primary-color);
        color: white;
        font-weight: 600;
        margin-top: 1rem;
        border-radius: var(--border-radius);
    }

    .total-amount {
        text-align: right;
        font-size: 1.1rem;
    }
    
    #performance-chart-container {
        background: var(--surface-elevated);
        padding: 2rem;
        border-radius: var(--border-radius-lg);
        margin: 2rem 0;
        box-shadow: var(--shadow-lg);
        border: 1px solid var(--border-color);
    }

    #performance-chart-container h3 {
        color: var(--text-primary);
        margin-bottom: 1.5rem;
        font-size: 1.5rem;
    }

    .performance-stats {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
        gap: 1.5rem;
        margin-top: 2rem;
        padding-top: 2rem;
        border-top: 1px solid var(--border-color);
    }

    .performance-stats .stat {
        text-align: center;
    }

    .performance-stats .stat h4 {
        color: var(--text-secondary);
        font-size: 0.875rem;
        font-weight: 500;
        margin-bottom: 0.5rem;
    }

    .performance-stats .stat span {
        color: var(--primary-color);
        font-size: 1.5rem;
        font-weight: 600;
    }

    
    #performance-chart-container h3 {
        color: var(--text-primary);
        margin-bottom: 1rem;
        font-size: 1.5rem;
    }
    
    .performance-stats {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
        gap: 1rem;
        margin-top: 2rem;
    }
    
    .performance-stats .stat {
        text-align: center;
        padding: 1rem;
        background: var(--surface-color);
        border-radius: var(--border-radius);
        border: 1px solid var(--border-color);
    }
    
    .performance-stats .stat h4 {
        font-size: 0.875rem;
        color: var(--text-secondary);
        margin-bottom: 0.5rem;
        font-weight: 500;
    }
    
    .performance-stats .stat span {
        font-size: 1.5rem;
        font-weight: 700;
        color: var(--text-primary);
    }
`;
document.head.appendChild(style);