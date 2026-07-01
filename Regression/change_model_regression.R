library(lmtest)
library(sandwich)


options(scipen = 999)

#load data
setwd(" ")

df_panel <- read.csv(" ")

df_panel_clean <- df_panel

df_panel_clean$Company.name <- as.factor(df_panel_clean$Company.name)
df_panel_clean$Branch <- as.factor(df_panel_clean$Branch)

dir.create(" ", showWarnings = FALSE)


#delta tone list
delta_tone_list <- c(
  "delta_tone_weighted",
  "delta_tone",
  "delta_tone_pos_weighted",
  "delta_tone_pos",
  "delta_tone_neg_weighted",
  "delta_tone_neg",
  "delta_tone_HENREY_weighted",
  "delta_tone_HENREY",
  "delta_tone_pos_HENREY_weighted",
  "delta_tone_pos_HENREY",
  "delta_tone_neg_HENREY_weighted",
  "delta_tone_neg_HENREY"
)



for (tone in delta_tone_list) {
  
  vars_this_model <- c(
    tone,
    "delta_roa",
    "delta_sale_growth",
    "delta_total_assets",
    "delta_leverage",
    "delta_book_to_market_ratio",
    "year",
    "Branch",
    "Company.name",
    "total_equity",
    "CEO_change_any"
  )
  
  df_panel_clean[] <- lapply(df_panel_clean, function(x) {
    
    if (is.numeric(x)) {
      
      x[is.infinite(x)] <- NA
      x[is.nan(x)] <- NA
      
    }
    
    x
  })
  
  
  #Exclude some false data only
  df_temp <- df_panel_clean[complete.cases(df_panel_clean[, vars_this_model]),]
  
  #order the data if not
  df_temp <- df_temp[order(df_temp$Company.name, df_temp$year), ]

  
  # Remove negative equity observations
  df_temp <- subset(
    df_temp,
    total_equity > 0
  )
  
  df_temp$year <- as.numeric(df_temp$year)
  
  df_temp <- df_temp[
    order(
      df_temp$Company.name,
      df_temp$year
    ),
  ]
  
  model_change <- lm(
    as.formula(
      paste0(
        tone,
        " ~ delta_roa +
          delta_sale_growth +
          delta_total_assets +
          delta_leverage +
          delta_book_to_market_ratio +
          CEO_change_any + 
          factor(year) +
          factor(Branch)"
      )
    ),
    data = df_temp
  )
  
  robust_results <- coeftest(
    model_change,
    vcov = vcovCL(
      model_change,
      cluster = df_temp$Company.name,
      type = "HC1"
    )
  )
  
  result_text <- c(
    "===================================",
    paste("DEPENDENT VARIABLE:", tone),
    "===================================",
    "",
    "===== OLS SUMMARY =====",
    capture.output(summary(model_change)),
    "",
    "===== CLUSTER-ROBUST RESULTS =====",
    capture.output(robust_results)
  )
  
  writeLines(
    result_text,
    paste0(
      "Regressions_Change_latest/",
      tone,
      "_OLS.txt"
    )
  )
}
