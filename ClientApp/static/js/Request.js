document.getElementById('data-query-form').addEventListener('submit', function(event) {
    event.preventDefault();

    const submitButton = document.getElementById('submit-button');
    const loadingIndicator = document.getElementById('loading');
    submitButton.disabled = true;
    loadingIndicator.style.display = 'block';

    const startDate = document.getElementById('start-date').value;
    const endDate = document.getElementById('end-date').value;
    const country = document.getElementById('country').value;
    const minAqi = parseInt(document.getElementById('min-aqi').value, 10) || 0;
    const maxAqi = parseInt(document.getElementById('max-aqi').value, 10) || 0;
    const range = document.getElementById('range').value;

    const formattedStartDate = formatDateForBackend(startDate);
    const formattedEndDate = formatDateForBackend(endDate);

    const requestData = {
        startDate: formattedStartDate,
        endDate: formattedEndDate,
        country,
        minAqi,
        maxAqi,
        range
    };

fetch('/api/query', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(requestData)
})
.then(response => {
        if (!response.ok) {
            // Log or print response for debugging
            console.error('Response Status:', response.status);
            return response.text().then(text => { throw new Error(text) });
        }
        return response.blob();
})
.then(blob => {
        downloadCSV(blob); // Trigger the download of the CSV file
})
.catch(error => {
        console.error('Error:', error);
        alert('An error occurred: ' + error.message);
})
.finally(() => {
        submitButton.disabled = false;
        loadingIndicator.style.display = 'none';
});
});

function formatDateForBackend(dateTimeString) {
    if (dateTimeString) {
        const formattedString = dateTimeString.replace('T', ' ');
        return formattedString + ':00';
    }
    return '';
}

function downloadCSV(blob) {
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'query_results.csv';
    document.body.appendChild(a);
    a.click();
    window.URL.revokeObjectURL(url);
}
