import pandas as pd

# Define the state and city data
stations_data = {
    "state": ["Andhra Pradesh", "Arunachal Pradesh", "Assam", "Bihar", "Chandigarh", "Chhattisgarh", "Delhi", "Gujarat", "Haryana", "Himachal Pradesh", "Jammu and Kashmir", "Jharkhand", "Karnataka", "Kerala", "Madhya Pradesh", "Maharashtra", "Manipur", "Meghalaya", "Mizoram", "Nagaland", "Odisha", "Puducherry", "Punjab", "Rajasthan", "Sikkim", "Tamil Nadu", "Telangana", "Tripura", "Uttar Pradesh", "Uttarakhand", "West Bengal"],
    "city": [
        "Amaravati,Anantapur,Chittoor,Kadapa,Rajamahendravaram,Tirupati,Vijayawada,Visakhapatnam",
        "Naharlagun",
        "Byrnihat,Guwahati,Nagaon,Nalbari,Silchar,Sivasagar",
        "Araria,Arrah,Aurangabad,Begusarai,Bettiah,Bhagalpur,Bihar Sharif,Buxar,Chhapra,Darbhanga,Gaya,Hajipur,Katihar,Kishanganj,Manguraha,Motihari,Munger,Muzaffarpur,Patna,Purnia,Rajgir,Saharsa,Samastipur,Sasaram,Siwan",
        "Chandigarh",
        "Bhilai,Bilaspur,Chhal,Korba,Kunjemura,Milupara,Raipur,Tumidih",
        "Delhi",
        "Ahmedabad,Ankleshwar,Gandhinagar,Nandesari,Surat,Vapi,Vatva",
        "Ambala,Bahadurgarh,Ballabgarh,Bhiwani,Charkhi Dadri,Dharuhera,Faridabad,Fatehabad,Gurugram,Hisar,Jind,Kaithal,Karnal,Kurukshetra,Mandikhera,Manesar,Narnaul,Palwal,Panchkula,Panipat,Rohtak,Sirsa,Sonipat,Yamuna Nagar",
        "Baddi",
        "Srinagar",
        "Dhanbad,Jorapokhar",
        "Bagalkot,Belgaum,Bengaluru,Bidar,Chamarajanagar,Chikkaballapur,Chikkamagaluru,Davanagere,Dharwad,Gadag,Hassan,Haveri,Hubballi,Kalaburagi,Kolar,Koppal,Madikeri,Mangalore,Mysuru,Raichur,Ramanagara,Shivamogga,Tumakuru,Udupi,Vijayapura,Yadgir",
        "Eloor,Ernakulam,Kannur,Kochi,Kollam,Kozhikode,Thiruvananthapuram,Thrissur",
        "Bhopal,Damoh,Dewas,Gwalior,Indore,Jabalpur,Katni,Maihar,Mandideep,Pithampur,Ratlam,Sagar,Satna,Singrauli,Ujjain",
        "Aurangabad,Chandrapur,Kalyan,Mumbai,Nagpur,Nashik,Navi Mumbai,Pune,Solapur,Thane",
        "Imphal",
        "Shillong",
        "Aizawl",
        "Kohima",
        "Baripada,Bileipada,Brajrajnagar,Keonjhar,Nayagarh,Rairangpur,Rourkela,Suakati,Talcher,Tensa",
        "Puducherry",
        "Amritsar,Bathinda,Jalandhar,Khanna,Ludhiana,Mandi Gobindgarh,Patiala,Rupnagar",
        "Ajmer,Alwar,Banswara,Barmer,Bharatpur,Bhiwadi,Bikaner,Chittorgarh,Churu,Dausa,Dholpur,Hanumangarh,Jaipur,Jaisalmer,Jhalawar,Jhunjhunu,Jodhpur,Karauli,Kota,Pali,Pratapgarh,Rajsamand,Sawai Madhopur,Sikar,Sirohi,Sri Ganganagar,Udaipur",
        "Gangtok",
        "Ariyalur,Chengalpattu,Chennai,Coimbatore,Cuddalore,Dindigul,Gummidipoondi,Hosur,Kanchipuram,Ooty,Palkalaiperur,Ramanathapuram,Salem,Thoothukudi,Tirupur,Vellore",
        "Hyderabad",
        "Agartala",
        "Agra,Baghpat,Bareilly,Bulandshahr,Firozabad,Ghaziabad,Gorakhpur,Greater Noida,Hapur,Jhansi,Kanpur,Khurja,Lucknow,Meerut,Moradabad,Muzaffarnagar,Noida,Prayagraj,Varanasi,Vrindavan",
        "Dehradun,Kashipur,Rishikesh",
        "Asansol,Durgapur,Haldia,Howrah,Kolkata,Siliguri"
    ]
}

# Create DataFrame
df = pd.DataFrame({
    "state": [],
    "city": [],
    "file_name": [],
    "agency": [],
    "station_location": [],
    "start_month": [],
    "start_month_num": [],
    "start_year": []
})

# Populate DataFrame
for state, cities in zip(stations_data["state"], stations_data["city"]):
    for city in cities.split(","):
        df = pd.concat([df, pd.DataFrame({
            "state": [state],
            "city": [city],
            "file_name": [f"{city.lower().replace(' ', '_')}_data.csv"],
            "agency": ["CPCB"],
            "station_location": [f"{city} Station"],
            "start_month": ["January"],
            "start_month_num": [1],
            "start_year": [2015]
        })], ignore_index=True)

# Save to CSV
df.to_csv("Stations_Info.csv", index=False)
print("Stations_Info.csv created successfully!")