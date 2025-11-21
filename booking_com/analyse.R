library(tidyverse)
library(lubridate)

# Folder with CSV files
data_folder <- "data"

# List CSV files
files <- list.files(path = data_folder, pattern = "\\.csv$", full.names = TRUE)

# Function to read and clean CSV
read_listing <- function(file) {
  df <- read_csv(file, col_types = cols(
    district = col_integer(),
    total_listings = col_integer(),
    entire_homes = col_integer()
  ))
  df <- df %>%
    mutate(date = ymd(basename(file) %>% str_remove("\\.csv"))) %>%
    mutate(across(c(total_listings, entire_homes), ~replace_na(.x, 0)))
  return(df)
}

# Read all data
all_data <- files %>% map_dfr(read_listing)

# Define groups
inner_city <- c(1,2,5,7,8,9,11,13)
district6 <- 6
outer_city <- setdiff(1:23, c(inner_city, district6))

all_data <- all_data %>%
  mutate(group = case_when(
    district == district6 ~ "District 6",
    district %in% inner_city ~ "Inner City",
    TRUE ~ "Outer City"
  ))

# ---------- Plot 1: Total Listings ----------
ggplot(all_data, aes(x = date, y = total_listings, group = factor(district), color = group)) +
  geom_line(size = 1) +
  geom_point(size = 1.5) +
  scale_color_manual(values = c("District 6" = "red",
                                "Inner City" = "orange",
                                "Outer City" = "lightgrey")) +
  labs(title = "Booking.com Total Listings Over Time by District",
       x = "Date",
       y = "Total Listings",
       color = "Group") +
  theme_minimal() +
  theme(text = element_text(size = 14))

# ---------- Plot 2: Entire Homes ----------
ggplot(all_data, aes(x = date, y = entire_homes, group = factor(district), color = group)) +
  geom_line(size = 1) +
  geom_point(size = 1.5) +
  scale_color_manual(values = c("District 6" = "red",
                                "Inner City" = "orange",
                                "Outer City" = "lightgrey")) +
  labs(title = "Booking.com Entire Homes Over Time by District",
       x = "Date",
       y = "Entire Homes",
       color = "Group") +
  theme_minimal() +
  theme(text = element_text(size = 14))

# ---------- Plot 3: Percentage of Entire Homes ----------
all_data <- all_data %>%
  mutate(entire_home_pct = ifelse(total_listings == 0, 0, entire_homes / total_listings * 100))

ggplot(all_data, aes(x = date, y = entire_home_pct, group = factor(district), color = group)) +
  geom_line(size = 1) +
  geom_point(size = 1.5) +
  scale_color_manual(values = c("District 6" = "red",
                                "Inner City" = "orange",
                                "Outer City" = "lightgrey")) +
  labs(title = "Percentage of Entire Homes Over Time by District",
       x = "Date",
       y = "Entire Homes (%)",
       color = "Group") +
  theme_minimal() +
  theme(text = element_text(size = 14))
