# GeoLens 🌍✨

GeoLens is an intelligent spatial knowledge explorer that connects places, stories, and ideas through space and time. It combines the power of spatial analysis, natural language processing, and knowledge graphs to help you discover fascinating connections in your data.

## 🎯 What is GeoLens?

GeoLens is a self-hosted platform that allows you to:
- Explore spatial data through natural language queries
- Discover hidden connections between locations
- Understand how ideas and influences spread across space and time
- Visualize complex spatial-temporal relationships

Example queries you can ask:
```
"Show me Gothic churches in Paris that influenced architecture in England"
"What historical events near the Thames are connected to maritime trade?"
"Find buildings similar to the Chrysler Building within 1km of Central Park"
```

## 🛠️ Technology Stack

GeoLens leverages cutting-edge open source technologies:
- **Spatial Analysis**: PostGIS for location-based queries
- **Natural Language**: Self-hosted Llama 3 for query understanding
- **Vector Search**: pgVector for semantic similarity
- **Graph Analysis**: Apache AGE for relationship queries
- **Frontend**: Vue.js with MapLibre GL for visualization
- **Backend**: FastAPI + Python

## 🌟 Key Features

- **Natural Language Interface**: Ask questions in plain English
- **Hybrid Search**: Combine spatial, semantic, and graph-based queries
- **Self-hosted**: Keep your data private and secure
- **Extensible**: Easy to add new data sources and relationship types
- **Interactive Visualization**: Explore connections through an intuitive map interface

## 🚀 Getting Started

### Prerequisites
- Python 3.10+
- PostgreSQL 15+ with PostGIS, pgVector, and AGE extensions
- Docker (optional, for running Llama 3)

### Quick Start
```bash
# Clone the repository
git clone https://github.com/yourusername/geolens.git
cd geolens

# Install dependencies using rye
rye sync

# Set up the database
rye run python scripts/setup_db.py

# Start the development server
rye run python -m geolens
```

## 📖 Documentation

For detailed documentation on setting up and using GeoLens, see our [docs](./docs/README.md).

## 🤝 Contributing

We welcome contributions! Please see our [Contributing Guide](./CONTRIBUTING.md) for details.

## 📄 License

GeoLens is licensed under the MIT License - see the [LICENSE](./LICENSE) file for details.

## 🙏 Acknowledgments

This project builds on several amazing open-source technologies:
- [Llama 3](https://github.com/facebookresearch/llama) by Meta AI
- [PostGIS](https://postgis.net/)
- [pgVector](https://github.com/pgvector/pgvector)
- [Apache AGE](https://age.apache.org/)
- [Vue.js](https://vuejs.org/)
- [MapLibre GL JS](https://maplibre.org/)

## 🔮 Project Status

GeoLens is currently in active development. We're working on:
- [ ] Core spatial query engine
- [ ] Natural language query parser
- [ ] Basic web interface
- [ ] Sample datasets
- [ ] Documentation

Stay tuned for updates!