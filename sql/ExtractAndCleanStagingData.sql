-- Temp table for flattened and cleaned data.
DROP TABLE IF EXISTS [dbo].[#TEMP_AllData]
CREATE TABLE #TEMP_AllData 
(
	[TweetId] numeric(20, 0) NOT NULL,
	[CreatedAt] datetime2 NULL,
	[Text] nvarchar(max) NULL,
	[RetweetCount] [int] NULL,
	[FavoriteCount] [int] NULL,
	[DummyVideo] [bit] NULL,
	[DummyImage] [bit] NULL,
	[QuotedStatusId] [numeric](20, 0) NULL,
	[InReplyToUserId] [numeric](20,0) NULL,

	[HashTags] varchar(600) NULL,
	[Symbols] varchar(600) NULL,
	[UserMentions] nvarchar(600) NULL,
	[Urls] nvarchar(max) NULL,

	[UserId] numeric(20,0) NULL,
	[UserName] varchar(20) NULL,
	[ScreenName] varchar(20) NULL,
	[ProfileImageUrl] varchar(2000) NULL,
	[Verified] Bit NULL
)
GO

-- Cast Json values to correct datatypes, 
-- deduplicate data and insert into temptable
WITH ALLDATA_DEDUPED AS (
	SELECT 
		vTweetId AS TweetId,				
		CAST(LEFT(JSON_VALUE(InfoJson, '$.created_at'), LEN(JSON_VALUE(InfoJson, '$.created_at'))-5) AS DATETIME ) AS CreatedAt, -- remove +0000, unessecary in next version
		JSON_VALUE(InfoJson, '$.text') AS [Text],
		JSON_VALUE(InfoJson, '$.retweet_count') AS RetweetCount,
		JSON_VALUE(InfoJson, '$.favorite_count') AS FavoriteCount,
		CAST(JSON_VALUE(InfoJson, '$.contains_video') AS Bit) AS DummyVideo,
		CAST(JSON_VALUE(InfoJson, '$.contains_photo') AS Bit) AS DummyImage,
		CAST(JSON_VALUE(InfoJson, '$.quoted_status_id_str') AS Numeric(20)) AS QuotedStatusId,
		JSON_VALUE(InfoJson, '$.in_reply_to_user_id') AS InReplyToUserId,

		JSON_QUERY(InfoJson, '$.entities.hashtags') AS HashTags,
		JSON_QUERY(InfoJson, '$.entities.symbols') AS Symbols,
		JSON_QUERY(InfoJson, '$.entities.user_mentions') AS UserMentions,
		JSON_QUERY(InfoJson, '$.entities.urls') AS Urls,

		CAST(JSON_VALUE(InfoJson, '$.user.id_str') AS Numeric(20)) AS UserId,
		JSON_VALUE(InfoJson, '$.user.name') AS UserName,
		JSON_VALUE(InfoJson, '$.user.screen_name') AS ScreenName,
		JSON_VALUE(InfoJson, '$.user.profile_image_url') AS ProfileImageUrl,
		CAST(JSON_VALUE(InfoJson, '$.user.verified') AS Bit) AS Verified,

		ROW_NUMBER() OVER ( PARTITION BY vTweetId ORDER BY vTweetId) AS OCCURENCE

	FROM Twitter_Staging_3
	WHERE DateProcessed is NULL
)
INSERT INTO #Temp_AllData
	SELECT 
		TweetId,
		CreatedAt,
		[Text],
		RetweetCount,
		FavoriteCount,
		DummyVideo,
		DummyImage,
		QuotedStatusId,
		InReplyToUserId,
		
		HashTags,
		Symbols,
		UserMentions,
		Urls,

		UserId,
		UserName,
		ScreenName,
		ProfileImageUrl,
		Verified

	FROM ALLDATA_DEDUPED
	WHERE OCCURENCE = 1
GO

DECLARE @datetimenow as datetime2
SET @datetimenow = GETDATE();


-- Insert any new Users
WITH NEW_USERS_DEDUPED AS (
	SELECT UserId, UserName, ScreenName, ProfileImageUrl, Verified,
		ROW_NUMBER() OVER ( PARTITION BY UserId ORDER BY UserId) AS OCCURENCE  
	FROM #Temp_AllData newData
	WHERE newData.UserId NOT IN
		(
		SELECT UserId
		FROM Twitter_Users
		)
)
INSERT INTO Twitter_Users (UserId, UserName, ScreenName, ProfileImageUrl, Verified, DateInjested)
SELECT UserId, UserName, ScreenName, ProfileImageUrl, Verified, @datetimenow AS DateInjested
	FROM NEW_USERS_DEDUPED
	WHERE OCCURENCE = 1

-- Insert any new Tweets
INSERT INTO Twitter_tweets (TweetId, UserId, CreatedAt, [Text], RetweetCount, FavoriteCount, DummyVideo, DummyImage, QuotedStatusId, InReplyToUserId, DateInjested)
SELECT TweetId, UserId, CreatedAt, [Text], RetweetCount, FavoriteCount, DummyVideo, DummyImage, QuotedStatusId, InReplyToUserId,  @datetimenow AS DateInjested
	FROM #TEMP_AllData newData
	WHERE newData.TweetId NOT IN
		(
		SELECT TweetId
		FROM Twitter_tweets
		)
GO

-- Insert any new Tweet Urls
INSERT INTO Tweet_Urls
SELECT * FROM 
(
	SELECT DISTINCT TweetId, Url, ExpandedUrl
	FROM #Temp_AllData
	CROSS APPLY OPENJSON(Urls)
		WITH (
			Url nvarchar(100) '$.url',
			ExpandedUrl nvarchar(240) '$.expanded_url'
			)
) AS newUrls
WHERE NOT EXISTS
(
	SELECT NULL
	FROM Tweet_Urls oldUrls
	WHERE oldUrls.TweetId = newUrls.TweetId 
	AND oldUrls.Url = newUrls.Url
)
GO

--Insert any new HashTags
INSERT INTO Tweet_Tags
SELECT * FROM 
(
	SELECT DISTINCT TweetId, value AS Tag
	FROM #Temp_AllData
	CROSS APPLY OPENJSON(HashTags)
) AS newTags
WHERE NOT EXISTS
(
	SELECT NULL
	FROM Tweet_Tags oldTags
	WHERE oldTags.TweetId = newTags.TweetId
	AND oldTags.Tag = newTags.Tag
)
GO

-- Insert any new Symbols
INSERT INTO Tweet_Tags
SELECT  * FROM 
(
	SELECT DISTINCT TweetId, value AS Tag
	FROM #Temp_AllData
	CROSS APPLY OPENJSON(Symbols)
) AS newTags
WHERE NOT EXISTS
(
	SELECT NULL
	FROM Tweet_Tags oldTags
	WHERE oldTags.TweetId = newTags.TweetId
	AND oldTags.Tag = newTags.Tag
)
GO

-- Insert any New UserMentions
INSERT INTO Tweet_UserMentions
SELECT * FROM 
(
	SELECT DISTINCT TweetId, UserId as SourceUserId, TargetUserId
	FROM #Temp_AllData
	CROSS APPLY OPENJSON(UserMentions)
	WITH(
		TargetUserId numeric(20, 0) '$.id_str'
	)
) AS newMentions
WHERE NOT EXISTS
(
	SELECT NULL
	FROM Tweet_UserMentions oldMentions
	WHERE oldMentions.TweetId = newMentions.TweetId
	AND oldMentions.SourceUserId = newMentions.SourceUserId
	AND oldMentions.TargetUserId = newMentions.TargetUserId
)

-- Mark records as processed in the staging table
DECLARE @datetimenow as datetime2
SET @datetimenow = GETDATE();

UPDATE Twitter_Staging_3
SET DateProcessed=@datetimenow
FROM Twitter_Staging_3 tst
INNER JOIN
	#Temp_AllData tad
ON
	CAST(JSON_VALUE(tst.InfoJson, '$.id_str') AS Numeric(20)) = tad.TweetId

DROP TABLE IF EXISTS [dbo].[#TEMP_AllData]
