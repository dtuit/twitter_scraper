DROP TABLE IF EXISTS [dbo].[Twitter_Staging]
DROP TABLE IF EXISTS [dbo].[Twitter_Statuses]
DROP TABLE IF EXISTS [dbo].[Twitter_Tweets]
DROP TABLE IF EXISTS [dbo].[Twitter_Users]
DROP TABLE IF EXISTS [dbo].[Tweet_Tags]
DROP TABLE IF EXISTS [dbo].[Tweet_Urls]
DROP TABLE IF EXISTS [dbo].[Tweet_UserMentions]

CREATE TABLE [dbo].[Twitter_Staging](
	[Id] [int] IDENTITY(1,1) NOT NULL,
	[InfoJson] [nvarchar](max) NOT NULL,
	[DateInjested] [datetime2](7) NOT NULL,
	[ProcessedFlag] [Bit] NOT NULL DEFAULT 'false'
	[DateProcessed] [datetime2](7) NULL
)
ALTER TABLE [dbo].[Twitter_Staging]
	ADD vTweetId AS CAST(JSON_VALUE(InfoJson, '$.id_str') AS Numeric(20))
CREATE INDEX idx_ts_json_TweetId ON [dbo].[Twitter_Staging](vTweetId) 
CREATE CLUSTERED INDEX idx_ts_DateProcessed ON [dbo].[Twitter_Staging](DateProcessed) 


CREATE TABLE [dbo].[Twitter_Users](
	[UserId] [numeric](20, 0) NOT NULL,
	[CreatedAt] [datetime2](7) NULL,
	[UserName] [varchar](20) NOT NULL,
	[ScreenName] [varchar](20) NULL,
	[ProfileImageUrl] [varchar](300) NULL,
	[Verified] [Bit] NULL,
	[DateInjested] [datetime2] NOT NULL, 
	[DateUpdated] [datetime2] NULL
	PRIMARY KEY (UserId)
)

CREATE TABLE [dbo].[Twitter_Tweets](
	[TweetId] [numeric](20, 0) NOT NULL,
	[UserId] [numeric](20, 0) NOT NULL,
	[CreatedAt] [datetime2](7) NOT NULL,
	[Text] [nvarchar](max) NOT NULL,
	[Sentiment] [nvarchar](max) NULL,
	[RetweetCount] [int] NULL,
	[FavoriteCount] [int] NULL,
	[DummyVideo] [bit] NULL,
	[DummyImage] [bit] NULL,
	[QuotedStatusId] [numeric](20, 0) NULL,
	[InReplyToUserId] [numeric](20,0) NULL,
	[DateInjested] [datetime2] NOT NULL, 
	[DateUpdated] [datetime2] NULL
	PRIMARY KEY (TweetId),
	CONSTRAINT FK_Tweets_Users FOREIGN KEY([UserId]) REFERENCES [dbo].[Twitter_Users] ([UserId])
)

CREATE TABLE [dbo].[Tweet_Tags](
	[TweetId] [numeric](20, 0) NOT NULL,
	[Tag] [varchar](140) NOT NULL
	PRIMARY KEY(TweetId, Tag)
)

CREATE TABLE [dbo].[Tweet_Urls](
	[TweetId] [numeric](20, 0) NOT NULL,
	[Url] [varchar](30) NOT NULL,
	[ExpandedUrl] [nvarchar](2000) NULL
	PRIMARY KEY (TweetId, [Url])
)

CREATE TABLE [dbo].[Tweet_UserMentions](
	[TweetId] [numeric](20, 0) NOT NULL,
	[SourceUserId] [numeric](20, 0) NOT NULL,
	[TargetUserId] [numeric](20, 0) NOT NULL,
	PRIMARY KEY(TweetId, SourceUserId, TargetUserId)
	-- If needs to be used as foreign key add surogate key with unique constraint
)