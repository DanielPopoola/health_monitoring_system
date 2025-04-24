import axios from 'axios';

const API_URL = 'http://localhost:8000/api/';

export const login = async (email, password) => {
    try {
        const response = await axios.post(`${API_URL}token/`, {
            email,
            password
        });

        if (response.data.access) {
            localStorage.setItem('user', JSON.stringify(response.data))
        }

        return response.data;
    } catch (error){
        throw error;
    }
};

export const register = async (first_name, last_name, age, gender, email, password) => {
    try {
        const name = `${first_name} ${last_name}`.trim();

        const response = await axios.post(`${API_URL}register/`, {
            first_name,
            last_name,
            name,
            age,
            gender,
            email,
            password
        });

        return response.data;
    } catch (error) {
        throw error;
    }
};


export const getCurrentUser = () => {
    return JSON.parse(localStorage.getItem('user'));
  };
  
  export const authHeader = () => {
    const user = JSON.parse(localStorage.getItem('user'));
    
    if (user && user.access) {
      return { Authorization: `Bearer ${user.access}` };
    } else {
      return {};
    }
};