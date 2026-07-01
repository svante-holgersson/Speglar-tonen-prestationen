library(nlme)
library(clubSandwich)

#load data
setwd(" ")

df_panel <- read.csv(" ")

df_panel_clean <- df_panel 

dir.create(" ", showWarnings = FALSE)


df_panel_clean$Company.name <- as.factor(df_panel_clean$Company.name)
df_panel_clean$Branch <- as.factor(df_panel_clean$Branch)
df_panel_clean$year <- as.factor(df_panel_clean$year)


#tone variables
tone_list <- c(
  "tone_weighted",
  "tone",
  "tone_pos_weighted",
  "tone_pos",
  "tone_neg_weighted",
  "tone_neg",
  "tone_HENREY_weighted",
  "tone_HENREY",
  "tone_pos_HENREY_weighted",
  "tone_pos_HENREY",
  "tone_neg_HENREY_weighted",
  "tone_neg_HENREY"
)


for (tone in tone_list) {
  
  vars_this_model <- c(
    tone,
    "roa",
    "sale_growth",
    "leverage",
    "firm_age",
    "ceo_tenure",
    "book_to_market_ratio",
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
  
  
  #df_temp <- subset(df_temp,CEO_change_any == 0)
  
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
  
  model_level <- lme(
    fixed = as.formula(
      paste0(
        tone,
        " ~ roa +
          sale_growth +
          leverage +
          firm_age +
          ceo_tenure +
          book_to_market_ratio +
          factor(year) +
          CEO_change_any +
          factor(Branch)"
      )
    ),
    
    random = ~1 | Company.name,
    
    correlation = corAR1(
      form = ~ year | Company.name
    ),
    
    data = df_temp,
    
    method = "REML",
    
    na.action = na.omit
  )
  
  robust_results <- coef_test(
    model_level,
    vcov = "CR2",
    cluster = df_temp$Company.name
  )
  
  result_text <- c(
    "===================================",
    paste("DEPENDENT VARIABLE:", tone),
    "===================================",
    "",
    "===== MODEL SUMMARY =====",
    capture.output(summary(model_level)),
    "",
    "===== CLUSTER-ROBUST CR2 RESULTS =====",
    capture.output(robust_results)
  )
  
  writeLines(
    result_text,
    paste0(
      "Regressions_Level_latest/",
      tone,
      "_LMM.txt"
    )
  )
}
