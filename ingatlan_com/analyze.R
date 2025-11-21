# Load required packages
library(dplyr)
library(stringr)
library(readr)
library(ggplot2)
library(purrr)
library(knitr)

# ---- 1. Load and process all CSV files ----
file_list <- list.files("data", pattern = "\\d{4}-\\d{2}-\\d{2}\\.csv$", full.names = TRUE)

process_file <- function(file_path) {
  date <- str_extract(basename(file_path), "\\d{4}-\\d{2}-\\d{2}") |> as.Date()
  
  read_csv(file_path) %>%
    mutate(
      price = str_remove_all(price, "Ft/hó| ") |> as.numeric(),
      district = str_extract(location, "Budapest\\s+([IVXLC]+)\\.\\s+kerület") |> 
        str_remove_all("Budapest\\s+|\\.\\s+kerület|\\s+"),
      alapterulet = str_remove(alapterulet, " m2") |> as.numeric(),
      erkely = str_remove(erkely, " m2") |> as.numeric(),
      price_sqm = price / alapterulet,
      date = date
    )
}

all_data <- map_dfr(file_list, process_file)

# ---- 2. Summary statistics ----
price_stats <- all_data %>%
  group_by(date, district) %>%
  summarise(
    mean_price = mean(price, na.rm = TRUE),
    median_price = median(price, na.rm = TRUE),
    mean_price_sqm = mean(price_sqm, na.rm = TRUE),
    median_price_sqm = median(price_sqm, na.rm = TRUE),
    n_listings = n(),
    .groups = "drop"
  ) %>%
  mutate(
    group = case_when(
      district == "VI" ~ "District VI",
      district %in% c("I","II","V","VII","VIII","IX","XI","XIII") ~ "Inner Budapest",
      TRUE ~ "Outer Budapest"
    )
  )

# ---- 3. Print a summary ----
kable(price_stats, digits = 0, caption = "Budapest District Rental Summary Over Time")

# ---- 4. Visualizations with ggplot2 ----
group_colors <- c(
  "District VI" = "red",
  "Inner Budapest" = "orange",
  "Outer Budapest" = "lightgrey"
)

# Mean price per m² over time
ggplot(price_stats, aes(x = date, y = mean_price_sqm, color = group, group = district)) +
  geom_line(size = 1) +
  geom_point(size = 2) +
  scale_color_manual(values = group_colors) +
  labs(
    title = "Mean Rent Price per m² Over Time by District",
    x = "Date",
    y = "Mean Price (Ft/m²)",
    color = "Group"
  ) +
  theme_minimal()

# Number of listings over time
ggplot(price_stats, aes(x = date, y = n_listings, color = group, group = district)) +
  geom_line(size = 1) +
  geom_point(size = 2) +
  scale_color_manual(values = group_colors) +
  labs(
    title = "Number of Listings Over Time by District",
    x = "Date",
    y = "Count of Listings",
    color = "Group"
  ) +
  theme_minimal()

# ---- Normalize values relative to first date ----
price_stats_rel <- price_stats %>%
  group_by(district) %>%
  arrange(date) %>%
  mutate(
    mean_price_sqm_rel = mean_price_sqm / first(mean_price_sqm) * 100,
    n_listings_rel = n_listings / first(n_listings) * 100
  ) %>%
  ungroup()

# ---- Relative Mean Price per m² Over Time ----
ggplot(price_stats_rel, aes(x = date, y = mean_price_sqm_rel, color = group, group = district)) +
  geom_line(size = 1) +
  geom_point(size = 2) +
  scale_color_manual(values = group_colors) +
  labs(
    title = "Relative Mean Rent Price per m² Over Time by District",
    x = "Date",
    y = "Relative Mean Price (% of first date)",
    color = "Group"
  ) +
  theme_minimal()

# ---- Relative Number of Listings Over Time ----
ggplot(price_stats_rel, aes(x = date, y = n_listings_rel, color = group, group = district)) +
  geom_line(size = 1) +
  geom_point(size = 2) +
  scale_color_manual(values = group_colors) +
  labs(
    title = "Relative Number of Listings Over Time by District",
    x = "Date",
    y = "Relative Listings (% of first date)",
    color = "Group"
  ) +
  theme_minimal()

