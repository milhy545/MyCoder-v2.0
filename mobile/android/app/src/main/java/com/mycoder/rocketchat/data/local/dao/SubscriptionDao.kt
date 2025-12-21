package com.mycoder.rocketchat.data.local.dao

import androidx.room.*
import com.mycoder.rocketchat.data.model.Subscription
import kotlinx.coroutines.flow.Flow

/**
 * Subscription Data Access Object
 */
@Dao
interface SubscriptionDao {

    @Query("SELECT * FROM subscriptions WHERE userId = :userId ORDER BY updatedAt DESC")
    fun getSubscriptionsForUser(userId: String): Flow<List<Subscription>>

    @Query("SELECT * FROM subscriptions WHERE roomId = :roomId AND userId = :userId")
    suspend fun getSubscription(roomId: String, userId: String): Subscription?

    @Insert(onConflict = OnConflictStrategy.REPLACE)
    suspend fun insertSubscription(subscription: Subscription)

    @Insert(onConflict = OnConflictStrategy.REPLACE)
    suspend fun insertSubscriptions(subscriptions: List<Subscription>)

    @Update
    suspend fun updateSubscription(subscription: Subscription)

    @Delete
    suspend fun deleteSubscription(subscription: Subscription)

    @Query("UPDATE subscriptions SET unread = :unread WHERE id = :subscriptionId")
    suspend fun updateUnread(subscriptionId: String, unread: Int)

    @Query("UPDATE subscriptions SET open = :open WHERE id = :subscriptionId")
    suspend fun updateOpen(subscriptionId: String, open: Boolean)
}
