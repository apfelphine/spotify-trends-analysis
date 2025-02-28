const map = L.map('map').setView([51.505, -0.09], 1);

const tiles = L.tileLayer('https://tile.openstreetmap.org/{z}/{x}/{y}.png', {
    maxZoom: 19,
    attribution: '&copy; <a href="http://www.openstreetmap.org/copyright">OpenStreetMap</a>'
}).addTo(map);

function getStyle(feature) {
    const pop = feature.properties.popularity;
    const shade = Math.round(255 * (1 - pop));

    return {
        fillColor: `rgb(${shade}, ${shade}, ${shade})`,
        color: "#000",
        weight: 1,
        fillOpacity: 0.8
    };
}

function formatPopularity(popularity) {
    if (Math.floor(popularity * 10000) !== popularity * 10000) {
        return popularity.toFixed(4);
    } else {
        return popularity.toString();
    }
}

function onEachFeature(feature, layer) {
    if (feature.properties) {
        const props = feature.properties;
        const popupContent = `
            <strong>${props.name} (${props.alpha_2_code})</strong><br>
            Popularity: ${formatPopularity(props.popularity)}
        `;

        layer.bindPopup(popupContent);
    }
}

function updateMap(artistId) {
    const loadButton = document.getElementById('fetchData');
    loadButton.disabled = true;
    const artistInput = document.getElementById('artistId');
    artistInput.disabled = true;
    const loadingIndicator = document.getElementById('loadingIndicator');
    loadingIndicator.style.display = 'block';

    map._handlers.forEach(function(handler) {
        handler.disable();
    });

    map.eachLayer(layer => {
        if (layer !== tiles) map.removeLayer(layer);
    });

    fetch(`http://localhost:8080/api/maps/popularity/artist/${artistId}`)
        .then(response => response.json())
        .then(data => {
            L.geoJSON(data, {
                style: getStyle,
                onEachFeature: onEachFeature
            }).addTo(map);
        })
        .catch(error => console.error("Error loading GeoJSON data:", error))
        .finally(() => {
            loadButton.disabled = false;
            artistInput.disabled = false;
            loadingIndicator.style.display = 'none';

            map._handlers.forEach(function(handler) {
                handler.enable();
            });
        });
}

// Initial data fetch with default artist
updateMap('4q3ewBCX7sLwd24euuV69X');

document.getElementById('fetchData').addEventListener('click', function() {
    const artistId = document.getElementById('artistId').value.trim();
    if (artistId) {
        updateMap(artistId);
    } else {
        alert("Please enter a valid Artist ID");
    }
});
