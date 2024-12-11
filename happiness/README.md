# Automated Analysis Report

Analysis for dataset: `happiness.csv`

## Dataset Overview
|        | Country name   |       year |   Life Ladder |   Log GDP per capita |   Social support |   Healthy life expectancy at birth |   Freedom to make life choices |     Generosity |   Perceptions of corruption |   Positive affect |   Negative affect |
|:-------|:---------------|-----------:|--------------:|---------------------:|-----------------:|-----------------------------------:|-------------------------------:|---------------:|----------------------------:|------------------:|------------------:|
| count  | 2363           | 2363       |    2363       |           2335       |      2350        |                         2300       |                    2327        | 2282           |                 2238        |       2339        |      2347         |
| unique | 165            |  nan       |     nan       |            nan       |       nan        |                          nan       |                     nan        |  nan           |                  nan        |        nan        |       nan         |
| top    | Argentina      |  nan       |     nan       |            nan       |       nan        |                          nan       |                     nan        |  nan           |                  nan        |        nan        |       nan         |
| freq   | 18             |  nan       |     nan       |            nan       |       nan        |                          nan       |                     nan        |  nan           |                  nan        |        nan        |       nan         |
| mean   | nan            | 2014.76    |       5.48357 |              9.39967 |         0.809369 |                           63.4018  |                       0.750282 |    9.77213e-05 |                    0.743971 |          0.651882 |         0.273151  |
| std    | nan            |    5.05944 |       1.12552 |              1.15207 |         0.121212 |                            6.84264 |                       0.139357 |    0.161388    |                    0.184865 |          0.10624  |         0.0871311 |
| min    | nan            | 2005       |       1.281   |              5.527   |         0.228    |                            6.72    |                       0.228    |   -0.34        |                    0.035    |          0.179    |         0.083     |
| 25%    | nan            | 2011       |       4.647   |              8.5065  |         0.744    |                           59.195   |                       0.661    |   -0.112       |                    0.687    |          0.572    |         0.209     |
| 50%    | nan            | 2015       |       5.449   |              9.503   |         0.8345   |                           65.1     |                       0.771    |   -0.022       |                    0.7985   |          0.663    |         0.262     |
| 75%    | nan            | 2019       |       6.3235  |             10.3925  |         0.904    |                           68.5525  |                       0.862    |    0.09375     |                    0.86775  |          0.737    |         0.326     |
| max    | nan            | 2023       |       8.019   |             11.676   |         0.987    |                           74.6     |                       0.985    |    0.7         |                    0.983    |          0.884    |         0.705     |

## Categorical Columns Distribution
### Distribution of 'Country name'
| Country name              |   proportion |
|:--------------------------|-------------:|
| Argentina                 |  0.00761744  |
| Costa Rica                |  0.00761744  |
| Brazil                    |  0.00761744  |
| Bolivia                   |  0.00761744  |
| Bangladesh                |  0.00761744  |
| Colombia                  |  0.00761744  |
| Chile                     |  0.00761744  |
| Cambodia                  |  0.00761744  |
| Cameroon                  |  0.00761744  |
| Canada                    |  0.00761744  |
| Saudi Arabia              |  0.00761744  |
| Russia                    |  0.00761744  |
| Philippines               |  0.00761744  |
| Zimbabwe                  |  0.00761744  |
| Thailand                  |  0.00761744  |
| Lithuania                 |  0.00761744  |
| Moldova                   |  0.00761744  |
| Mexico                    |  0.00761744  |
| Kenya                     |  0.00761744  |
| Lebanon                   |  0.00761744  |
| Kyrgyzstan                |  0.00761744  |
| Israel                    |  0.00761744  |
| Italy                     |  0.00761744  |
| Jordan                    |  0.00761744  |
| Japan                     |  0.00761744  |
| Kazakhstan                |  0.00761744  |
| Ghana                     |  0.00761744  |
| Indonesia                 |  0.00761744  |
| India                     |  0.00761744  |
| Germany                   |  0.00761744  |
| France                    |  0.00761744  |
| Georgia                   |  0.00761744  |
| El Salvador               |  0.00761744  |
| Dominican Republic        |  0.00761744  |
| Ecuador                   |  0.00761744  |
| Egypt                     |  0.00761744  |
| Denmark                   |  0.00761744  |
| South Africa              |  0.00761744  |
| South Korea               |  0.00761744  |
| Spain                     |  0.00761744  |
| Sweden                    |  0.00761744  |
| Tajikistan                |  0.00761744  |
| Tanzania                  |  0.00761744  |
| United Kingdom            |  0.00761744  |
| Türkiye                   |  0.00761744  |
| United States             |  0.00761744  |
| Uruguay                   |  0.00761744  |
| Venezuela                 |  0.00761744  |
| Vietnam                   |  0.00761744  |
| Uganda                    |  0.00761744  |
| Ukraine                   |  0.00761744  |
| Nicaragua                 |  0.00761744  |
| Nepal                     |  0.00761744  |
| Peru                      |  0.00761744  |
| Pakistan                  |  0.00761744  |
| Senegal                   |  0.00761744  |
| New Zealand               |  0.00719424  |
| Sri Lanka                 |  0.00719424  |
| Uzbekistan                |  0.00719424  |
| Latvia                    |  0.00719424  |
| Australia                 |  0.00719424  |
| Armenia                   |  0.00719424  |
| Belgium                   |  0.00719424  |
| China                     |  0.00719424  |
| Netherlands               |  0.00719424  |
| Romania                   |  0.00719424  |
| Poland                    |  0.00719424  |
| Paraguay                  |  0.00719424  |
| Panama                    |  0.00719424  |
| Honduras                  |  0.00719424  |
| Greece                    |  0.00719424  |
| Kosovo                    |  0.00719424  |
| Hungary                   |  0.00719424  |
| Ireland                   |  0.00719424  |
| Estonia                   |  0.00719424  |
| Zambia                    |  0.00719424  |
| Mali                      |  0.00719424  |
| Guatemala                 |  0.00677105  |
| North Macedonia           |  0.00677105  |
| Nigeria                   |  0.00677105  |
| United Arab Emirates      |  0.00677105  |
| State of Palestine        |  0.00677105  |
| Taiwan Province of China  |  0.00677105  |
| Slovenia                  |  0.00677105  |
| Iran                      |  0.00677105  |
| Austria                   |  0.00677105  |
| Azerbaijan                |  0.00677105  |
| Bosnia and Herzegovina    |  0.00677105  |
| Burkina Faso              |  0.00677105  |
| Albania                   |  0.00677105  |
| Chad                      |  0.00677105  |
| Croatia                   |  0.00677105  |
| Singapore                 |  0.00677105  |
| Portugal                  |  0.00677105  |
| Serbia                    |  0.00677105  |
| Niger                     |  0.00677105  |
| Cyprus                    |  0.00677105  |
| Malaysia                  |  0.00677105  |
| Mongolia                  |  0.00677105  |
| Finland                   |  0.00677105  |
| Bulgaria                  |  0.00634786  |
| Malawi                    |  0.00634786  |
| Malta                     |  0.00634786  |
| Mauritania                |  0.00634786  |
| Montenegro                |  0.00634786  |
| Tunisia                   |  0.00634786  |
| Slovakia                  |  0.00634786  |
| Iraq                      |  0.00634786  |
| Czechia                   |  0.00634786  |
| Benin                     |  0.00634786  |
| Afghanistan               |  0.00634786  |
| Sierra Leone              |  0.00634786  |
| Yemen                     |  0.00592467  |
| Belarus                   |  0.00592467  |
| Congo (Brazzaville)       |  0.00592467  |
| Botswana                  |  0.00592467  |
| Madagascar                |  0.00550148  |
| Switzerland               |  0.00550148  |
| Norway                    |  0.00550148  |
| Hong Kong S.A.R. of China |  0.00550148  |
| Morocco                   |  0.00550148  |
| Gabon                     |  0.00550148  |
| Guinea                    |  0.00550148  |
| Kuwait                    |  0.00550148  |
| Luxembourg                |  0.00550148  |
| Ivory Coast               |  0.00507829  |
| Bahrain                   |  0.00507829  |
| Myanmar                   |  0.00507829  |
| Togo                      |  0.00507829  |
| Rwanda                    |  0.00507829  |
| Laos                      |  0.00507829  |
| Algeria                   |  0.0046551   |
| Mozambique                |  0.0046551   |
| Liberia                   |  0.0046551   |
| Haiti                     |  0.0046551   |
| Iceland                   |  0.0046551   |
| Ethiopia                  |  0.0046551   |
| Mauritius                 |  0.00423191  |
| Turkmenistan              |  0.00423191  |
| Congo (Kinshasa)          |  0.00423191  |
| Namibia                   |  0.00380872  |
| Jamaica                   |  0.00380872  |
| Libya                     |  0.00338553  |
| Comoros                   |  0.00338553  |
| Syria                     |  0.00296234  |
| Burundi                   |  0.00211595  |
| Central African Republic  |  0.00211595  |
| Sudan                     |  0.00211595  |
| Trinidad and Tobago       |  0.00211595  |
| Gambia                    |  0.00211595  |
| Lesotho                   |  0.00211595  |
| Qatar                     |  0.00211595  |
| Angola                    |  0.00169276  |
| South Sudan               |  0.00169276  |
| Somaliland region         |  0.00169276  |
| Eswatini                  |  0.00169276  |
| Djibouti                  |  0.00169276  |
| Bhutan                    |  0.00126957  |
| Somalia                   |  0.00126957  |
| Belize                    |  0.000846382 |
| Cuba                      |  0.000423191 |
| Maldives                  |  0.000423191 |
| Guyana                    |  0.000423191 |
| Oman                      |  0.000423191 |
| Suriname                  |  0.000423191 |

## Correlation Matrix
|                                  |       year |   Life Ladder |   Log GDP per capita |   Social support |   Healthy life expectancy at birth |   Freedom to make life choices |   Generosity |   Perceptions of corruption |   Positive affect |   Negative affect |
|:---------------------------------|-----------:|--------------:|---------------------:|-----------------:|-----------------------------------:|-------------------------------:|-------------:|----------------------------:|------------------:|------------------:|
| year                             |  1         |     0.0468461 |          0.0801038   |       -0.0430737 |                          0.168026  |                       0.232974 |  0.0308644   |                  -0.0821355 |         0.0130525 |         0.207642  |
| Life Ladder                      |  0.0468461 |     1         |          0.783556    |        0.722738  |                          0.714927  |                       0.53821  |  0.177398    |                  -0.430485  |         0.515283  |        -0.352412  |
| Log GDP per capita               |  0.0801038 |     0.783556  |          1           |        0.685329  |                          0.819326  |                       0.364816 | -0.000765985 |                  -0.353893  |         0.230868  |        -0.260689  |
| Social support                   | -0.0430737 |     0.722738  |          0.685329    |        1         |                          0.597787  |                       0.404131 |  0.0652399   |                  -0.22141   |         0.424524  |        -0.454878  |
| Healthy life expectancy at birth |  0.168026  |     0.714927  |          0.819326    |        0.597787  |                          1         |                       0.375745 |  0.0151682   |                  -0.30313   |         0.217982  |        -0.15033   |
| Freedom to make life choices     |  0.232974  |     0.53821   |          0.364816    |        0.404131  |                          0.375745  |                       1        |  0.321396    |                  -0.466023  |         0.578398  |        -0.278959  |
| Generosity                       |  0.0308644 |     0.177398  |         -0.000765985 |        0.0652399 |                          0.0151682 |                       0.321396 |  1           |                  -0.270004  |         0.300608  |        -0.0719746 |
| Perceptions of corruption        | -0.0821355 |    -0.430485  |         -0.353893    |       -0.22141   |                         -0.30313   |                      -0.466023 | -0.270004    |                   1         |        -0.274208  |         0.265555  |
| Positive affect                  |  0.0130525 |     0.515283  |          0.230868    |        0.424524  |                          0.217982  |                       0.578398 |  0.300608    |                  -0.274208  |         1         |        -0.334451  |
| Negative affect                  |  0.207642  |    -0.352412  |         -0.260689    |       -0.454878  |                         -0.15033   |                      -0.278959 | -0.0719746   |                   0.265555  |        -0.334451  |         1         |

