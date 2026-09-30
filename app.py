import streamlit as st
import pickle
import pandas as pd
import requests

st.set_page_config(layout="wide", page_title="Movie Recommender")

# CSS
st.markdown("""
<style>
/* Grid container for the cards */
.movie-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
    gap: 20px;
    margin-top: 20px;
}

/* Elegant Light Card Design */
.elegant-card {
    background-color: #ffffff;
    border-radius: 12px;
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08);
    display: flex;
    flex-direction: column;
    overflow: hidden;
    border: 1px solid #f0f0f0;
    transition: transform 0.2s, box-shadow 0.2s;
    height: 100%;
}

.elegant-card:hover {
    transform: translateY(-5px);
    box-shadow: 0 8px 24px rgba(0, 0, 0, 0.12);
}

.elegant-poster {
    width: 100%;
    aspect-ratio: 2 / 3;
    object-fit: cover;
}

/* Container for text info below the poster */
.elegant-info {
    padding: 15px;
    display: flex;
    flex-direction: column;
    flex-grow: 1;
    align-items: center;
    text-align: center;
}

.elegant-title {
    font-size: 16px;
    font-weight: 600;
    color: #333333;
    margin-bottom: 6px;
}

.elegant-rating {
    font-size: 14px;
    color: #ff9900;
    font-weight: bold;
    margin-bottom: 6px;
}

.elegant-cast {
    font-size: 12px;
    color: #777777;
    margin-bottom: 15px;
    flex-grow: 1;
}

.watch-btn {
    display: inline-block;
    padding: 8px 16px;
    background-color: #ff4b4b;
    color: white !important;
    text-decoration: none !important;
    border-radius: 6px;
    font-size: 14px;
    font-weight: 500;
    transition: background-color 0.2s;
}

.watch-btn:hover {
    background-color: #ff3333;
}
</style>
""", unsafe_allow_html=True)

def fetch_movie_info(movie_id):
    api_key = st.secrets["TMDB_API_KEY"]
    url = f"https://api.themoviedb.org/3/movie/{movie_id}?api_key={api_key}&language=en-US&append_to_response=videos,credits"
    
    try:
        data = requests.get(url).json()
        
        poster_path = data.get('poster_path')
        if poster_path:
            full_path = "https://image.tmdb.org/t/p/w500/" + poster_path
        else:
            full_path = "https://placehold.co/500x750/eeeeee/333333.png?text=No+Poster"
            
        rating = round(data.get('vote_average', 0), 1)
        
        trailer_key = None
        if 'videos' in data and 'results' in data['videos']:
            for video in data['videos']['results']:
                if video['type'] == 'Trailer' and video['site'] == 'YouTube':
                    trailer_key = video['key']
                    break
                    
        cast = []
        director = "Unknown Director"
        if 'credits' in data:
            if 'cast' in data['credits']:
                for c in data['credits']['cast'][:3]:
                    cast.append(c['name'])
            if 'crew' in data['credits']:
                for member in data['credits']['crew']:
                    if member['job'] == 'Director':
                        director = member['name']
                        break
                
        return full_path, rating, trailer_key, cast, director
    
    except Exception:
        return "https://placehold.co/500x750/eeeeee/ff0000.png?text=Error", "N/A", None, [], "Unknown Director"

def recommend(movie):
    movie_index = movies[movies['title'] == movie].index[0]
    distances = similarity[movie_index]
    movies_list = sorted(list(enumerate(distances)), reverse=True, key=lambda x: x[1])[1:6]

    recommended_movies = []
    for i in movies_list:
        movie_id = movies.iloc[i[0]].movie_id
        title = movies.iloc[i[0]].title
        poster, rating, trailer, cast, director = fetch_movie_info(movie_id)
        
        recommended_movies.append({
            'title': title,
            'poster': poster,
            'rating': rating,
            'trailer': trailer,
            'cast': cast,
            'director': director
        })
        
    return recommended_movies

@st.cache_data
def load_data():
    try:
        movies_dict = pickle.load(open('movie_dict.pkl', 'rb'))
        movies_df = pd.DataFrame(movies_dict)
        sim_matrix = pickle.load(open('similarity.pkl', 'rb'))
        return movies_df, sim_matrix
    except FileNotFoundError:
        return None, None

movies, similarity = load_data()

if movies is None or similarity is None:
    st.error("Model files not found! Please make sure to export 'movie_dict.pkl' and 'similarity.pkl' from your notebook first.")
    st.stop()

st.title('Movie Recommender')
st.markdown("Find similar movies based on your favorites.")

# Input Box
input_col, empty_col = st.columns([1, 2])
with input_col:
    selected_movie_name = st.selectbox(
        'Select a movie:',
        movies['title'].values
    )

if st.button('Recommend'):
    with st.spinner('Fetching recommendations...'):
        recommendations = recommend(selected_movie_name)
        
        # Cards
        html_content = '<div class="movie-grid">\n'
        
        for movie in recommendations:
            trailer_html = f'<a href="https://www.youtube.com/watch?v={movie["trailer"]}" target="_blank" class="watch-btn">▶ Trailer</a>' if movie['trailer'] else ''
            cast_str = ", ".join(movie['cast']) if movie['cast'] else "Unknown Cast"
            director_str = movie['director']
            
            card_html = f'''<div class="elegant-card">
<img src="{movie['poster']}" class="elegant-poster">
<div class="elegant-info">
<div class="elegant-title">{movie['title']}</div>
<div class="elegant-rating">⭐ {movie['rating']} / 10</div>
<div class="elegant-cast"><strong>Director:</strong> {director_str}<br><strong>Cast:</strong> {cast_str}</div>
{trailer_html}
</div>
</div>
'''
            html_content += card_html
            
        html_content += '</div>'
        
        st.markdown(html_content, unsafe_allow_html=True)
